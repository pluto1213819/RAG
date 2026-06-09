from typing import List, Dict, Union
import chromadb
import math
import os
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DIR = os.path.join(PROJECT_ROOT, "chroma_data")


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
        text = text.lower()
        chinese = re.findall(r'[\u4e00-\u9fff]+', text)
        tokens = []
        for seg in chinese:
            for ch in seg:
                tokens.append(ch)
            for i in range(len(seg) - 1):
                tokens.append(seg[i:i+2])
            for i in range(len(seg) - 2):
                tokens.append(seg[i:i+3])
        english = re.findall(r'[a-z0-9]+', text)
        tokens.extend(english)
        return tokens


_ef_instance = None

def _ef():
    global _ef_instance
    if _ef_instance is None:
        _ef_instance = TfidfEmbedding()
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
