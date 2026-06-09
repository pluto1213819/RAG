from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from app.db import get_db
from app.models import Document
from app.schemas.documents import DocumentCreate, DocumentRead, QueryRequest, QueryResponse, SourceItem
from rag_core.vector_store import ingest_texts, retrieve
from rag_core.reranker import rerank
from app.services.llm import get_llm_client, get_llm_model

router = APIRouter(prefix="/api", tags=["docs"])

RETRIEVAL_TOP_K = 5
RERANK_TOP_K = 3


def _build_rag_prompt(query, sources):
    context = ""
    for i, s in enumerate(sources, 1):
        context += f"[来源{i}] {s.content}\n\n"
    return f"""你是一个专业的 AI 助手。请基于以下检索到的证据，回答用户的问题。
要求：1. 回答必须基于提供的证据 2. 标注引用来源 3. 结构清晰
检索到的证据：
{context}
用户问题：{query}
请基于以上证据回答："""


def _generate_answer(query, sources):
    try:
        client = get_llm_client()
        model = get_llm_model()
        prompt = _build_rag_prompt(query, sources)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        return "LLM 调用失败: %s" % str(e)


def _get_confidence_footer(max_score):
    if max_score >= 0.35:
        return ""
    elif max_score >= 0.2:
        return "\n\n---\n⚠️ 回答仅供参考，知识库中相关内容有限，建议进一步核实。"
    elif max_score >= 0.1:
        return "\n\n---\n⚠️ 回答不太准确，知识库中匹配到的内容相关度较低，仅供参考。"
    else:
        return "\n\n---\n❌ 回答可能不准确，知识库中几乎没有匹配内容，建议导入更多相关资料。"


@router.get("/docs", response_model=List[DocumentRead])
def list_docs(db: Session = Depends(get_db)):
    return db.query(Document).all()


@router.post("/docs", response_model=DocumentRead)
def create_doc(body: DocumentCreate, db: Session = Depends(get_db)):
    d = Document(title=body.title, path=body.path, metadata_=body.metadata or {})
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.post("/docs/{doc_id}/index")
def index_doc(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(404, "Doc not found")
    with open(doc.path, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
    ingest_texts(doc.id, chunks, metadata={"title": doc.title, "path": doc.path})
    return {"status": "ok", "chunks_indexed": len(chunks)}


@router.post("/query", response_model=QueryResponse)
def query_docs(body: QueryRequest, db: Session = Depends(get_db)):
    # Step 1: 向量检索（召回 5 条）
    results = retrieve(body.query, top_k=RETRIEVAL_TOP_K)

    if not results:
        return QueryResponse(
            answer="知识库为空，无法回答。请先导入文档。",
            sources=[],
            metrics={"step": "retrieval", "status": "empty", "retrieval_count": 0, "rerank_count": 0}
        )

    retrieval_count = len(results)

    # Step 2: BM25 + 向量混合重排（取 top 3）
    reranked = rerank(body.query, results, top_k=RERANK_TOP_K)
    rerank_count = len(reranked)

    # 构建 sources
    sources = []
    for r in reranked:
        sc = r.get("rerank_score", 0)
        sources.append(SourceItem(content=r["content"], source=r["metadata"].get("path", ""), score=sc))

    scores = [s.score or 0 for s in sources]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0

    # Step 3: LLM 生成回答
    answer = _generate_answer(body.query, sources)

    # Step 4: 置信度提示
    answer += _get_confidence_footer(max_score)

    if max_score >= 0.35:
        confidence_level = "high"
    elif max_score >= 0.2:
        confidence_level = "medium"
    elif max_score >= 0.1:
        confidence_level = "low"
    else:
        confidence_level = "very_low"

    return QueryResponse(
        answer=answer,
        sources=sources,
        metrics={
            "step": "completed",
            "llm_generated": True,
            "confidence": confidence_level,
            "retrieval_count": retrieval_count,
            "rerank_count": rerank_count,
            "evidence_count": len(sources),
            "avg_score": round(avg_score, 4),
            "max_score": round(max_score, 4)
        }
    )
