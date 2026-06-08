from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document, User
from app.schemas.documents import DocumentCreate, DocumentRead, QueryRequest, QueryResponse, SourceItem
from app.auth import get_current_user
from rag_core.vector_store import ingest_texts, retrieve

router = APIRouter(prefix="/api/docs", tags=["docs"])


@router.get("/", response_model=List[DocumentRead])
def list_docs(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Document).filter(Document.tenant_id == user.tenant_id).all()


@router.post("/", response_model=DocumentRead)
def create_doc(body: DocumentCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = Document(tenant_id=user.tenant_id, title=body.title, path=body.path, metadata_=body.metadata or {})
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.post("/{doc_id}/index")
def index_doc(doc_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.tenant_id == user.tenant_id).first()
    if not doc:
        raise HTTPException(404, "Doc not found")
    with open(doc.path, "r", encoding="utf-8") as f:
        text = f.read()
    chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
    ingest_texts(user.tenant_id, doc.id, chunks, metadata={"title": doc.title, "path": doc.path})
    return {"status": "ok", "chunks_indexed": len(chunks)}


@router.post("/query", response_model=QueryResponse)
def query_docs(body: QueryRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    results = retrieve(user.tenant_id, body.query, top_k=body.top_k)
    if not results:
        return QueryResponse(answer="No relevant evidence found.", sources=[], metrics={"tool": "vector_retrieve"})
    sources = [SourceItem(content=r["content"], source=r["metadata"].get("path", ""), score=r.get("score")) for r in results]
    answer = f"基于检索到的 {len(sources)} 条证据回答（示例）：\n- " + "\n- ".join(s.content[:120] for s in sources)
    return QueryResponse(answer=answer, sources=sources, metrics={"top_k": body.top_k})
