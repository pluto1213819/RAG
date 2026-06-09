import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from rag_core.reranker import rerank
from rag_core.vector_store import retrieve

query = "Agent 有哪些架构模式？"
results = retrieve(1, query, top_k=5)

print("Retrieved %d results" % len(results))
for i, r in enumerate(results):
    print("  %d: content=%s" % (i, r["content"][:40]))

reranked = rerank(query, results, top_k=3)
print("\nReranked %d results" % len(reranked))
for i, r in enumerate(reranked):
    print("  %d: score=%s content=%s" % (i, r.get("rerank_score"), r["content"][:40]))
