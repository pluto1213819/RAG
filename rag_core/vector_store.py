"""向量存储：用 Ollama bge-m3 生成 1024 维嵌入"""
import chromadb
import os
import requests
from typing import List, Dict

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")
CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_data"))


class OllamaEmbedding:
    """通过 Ollama API 调用 bge-m3 生成嵌入向量"""

    def __init__(self, model: str = EMBED_MODEL):
        self.model = model

    def name(self) -> str:
        return f"ollama-{self.model}"

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embed(input)

    def embed(self, input: List[str]) -> List[List[float]]:
        results = []
        for text in input:
            resp = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=60,
            )
            resp.raise_for_status()
            results.append(resp.json()["embedding"])
        return results

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self.embed(input)

    def embed_query(self, input) -> List[List[float]]:
        if isinstance(input, list):
            input = input[0]
        return self.embed([input])


_ef_instance = None


def _ef():
    global _ef_instance
    if _ef_instance is None:
        _ef_instance = OllamaEmbedding()
    return _ef_instance


_client = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
    return _client


COLLECTION = "knowledge_base"


def get_collection():
    return _get_client().get_or_create_collection(
        name=COLLECTION,
        embedding_function=_ef(),
        metadata={"hnsw:space": "cosine"}
    )


def ingest_texts(doc_id: int, texts: List[str], metadata: Dict | None = None):
    col = get_collection()
    metadata = metadata or {}
    for i, text in enumerate(texts):
        cid = f"{doc_id}_{i}"
        col.upsert(
            documents=[text],
            ids=[cid],
            metadatas=[{"doc_id": doc_id, "chunk_id": i, **metadata}],
        )


def retrieve(query: str, top_k: int = 3):
    col = get_collection()
    res = col.query(query_texts=[query], n_results=top_k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0] if "distances" in res else []
    out = []
    for idx, (d, m) in enumerate(zip(docs, metas)):
        score = 1.0 - dists[idx] if idx < len(dists) else 0.0
        out.append({
            "content": d,
            "metadata": m,
            "score": round(score, 4),
        })
    return out
