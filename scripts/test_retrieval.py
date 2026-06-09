import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ".")
from rag_core.vector_store import retrieve

queries = [
    "Agent 有哪些架构模式？",
    "什么是 RAG？",
    "Agent 怎么调用工具？",
]
for q in queries:
    results = retrieve(1, q, top_k=2)
    print(f"\nQuery: {q}")
    for r in results:
        print(f"  score={r['score']:.4f} | {r['metadata'].get('title','?')} | {r['content'][:60]}")
