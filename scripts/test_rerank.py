import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from rag_core.vector_store import retrieve
from rag_core.reranker import rerank

query = "Agent 有哪些架构模式？"
results = retrieve(1, query, top_k=5)
reranked = rerank(query, results, top_k=3)
for r in reranked:
    score = r.get("rerank_score")
    content = r["content"][:60]
    print(f"  score={score} | {content}")
