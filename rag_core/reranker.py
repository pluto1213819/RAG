"""重排器：基于 bge-m3 嵌入的交叉相似度重排"""
import os
import requests
import numpy as np
from typing import List

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")


def _get_embedding(text: str) -> List[float]:
    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embedding"]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    dot = float(np.dot(a, b))
    norm = float(np.linalg.norm(a) * np.linalg.norm(b))
    return dot / norm if norm > 0 else 0.0


def rerank(query: str, candidates: List[dict], top_k: int = 3) -> List[dict]:
    """用 bge-m3 对候选片段做交叉相似度重排"""
    if not candidates:
        return []

    query_vec = _get_embedding(query)

    scored = []
    for c in candidates:
        content = c.get("content", "")
        doc_vec = _get_embedding(content)
        sim = _cosine_similarity(query_vec, doc_vec)

        # 融合原始检索分数（权重 0.3）和交叉嵌入分数（权重 0.7）
        raw_score = c.get("score", 0)
        hybrid = 0.3 * raw_score + 0.7 * sim
        scored.append({**c, "rerank_score": round(hybrid, 4)})

    scored.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    return scored[:top_k]
