from typing import List, Dict, Union
import chromadb
import math
import os
import re


class TfidfEmbedding:
    def __init__(self, dim: int = 256):
        self.dim = dim
        self.vocab: Dict[str, int] = {}

    def name(self) -> str:
        return "tfidf-lite"

    def __call__(self, input: List[str]) -> List[List[float]]:
        return self.embed(input)

    def embed(self, input: List[str]) -> List[List[float]]:
        tokens_list = [self._tokenize(text) for text in input]
        all_tokens = set()
        for tokens in tokens_list:
            all_tokens.update(tokens)
        self.vocab = {t: i % self.dim for i, t in enumerate(sorted(all_tokens))}
        results = []
        for tokens in tokens_list:
            vec = [0.0] * self.dim
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            for t, count in tf.items():
                if t in self.vocab:
                    vec[self.vocab[t]] = 1.0 + math.log(count)
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vec = [v / norm for v in vec]
            results.append(vec)
        return results

    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self.embed(input)

    def embed_query(self, input: Union[str, List[str]]) -> List[List[float]]:
        if isinstance(input, list):
            input = input[0]
        return self.embed([input])

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9\u4e00-\u9fff]+", text.lower())


def _ef():
    return TfidfEmbedding()


def _client():
    chroma_dir = os.getenv("CHROMA_DIR", "chroma_data")
    return chromadb.PersistentClient(path=chroma_dir)


def collection_name(tenant_id: int) -> str:
    return f"tenant_{tenant_id}"


def get_collection(tenant_id: int):
    return _client().get_or_create_collection(
        name=collection_name(tenant_id), embedding_function=_ef()
    )


def ingest_texts(tenant_id: int, doc_id: int, texts: List[str], metadata: Dict | None = None):
    col = get_collection(tenant_id)
    metadata = metadata or {}
    for i, text in enumerate(texts):
        cid = f"{doc_id}_{i}"
        col.upsert(
            documents=[text],
            ids=[cid],
            metadatas=[{"doc_id": doc_id, "chunk_id": i, **metadata}],
        )


def retrieve(tenant_id: int, query: str, top_k: int = 3):
    col = get_collection(tenant_id)
    res = col.query(query_texts=[query], n_results=top_k)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0] if "distances" in res else []
    out = []
    for idx, (d, m) in enumerate(zip(docs, metas)):
        out.append({
            "content": d,
            "metadata": m,
            "score": dists[idx] if idx < len(dists) else None,
        })
    return out
