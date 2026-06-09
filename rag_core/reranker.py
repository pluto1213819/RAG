from typing import List
import re
import math

STOPWORDS = set("的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 会 着 没有 看 好 自己 这 他 她 它 们 那 里 为 什么 吗 个 之 与 及 或 等 把 被 让 给 对 从 以 而 但 又 如 所 能 可 这个 那个 这些 那些 什么 怎么 为什么 哪 哪些".split())

BM25_WEIGHT = 0.4
COSINE_WEIGHT = 0.6


def rerank(query: str, candidates: List[dict], top_k: int = 3) -> List[dict]:
    """混合重排：BM25 关键词匹配 + 原始向量相似度"""
    if not candidates:
        return []

    query_terms = _extract_terms(query)

    if not query_terms:
        # 无关键词可提取时，按原始 score 排序
        sorted_cands = sorted(candidates, key=lambda x: x.get("score", 0), reverse=True)
        for c in sorted_cands:
            c["rerank_score"] = c.get("score", 0)
        return sorted_cands[:top_k]

    doc_count = len(candidates)
    doc_freq = _compute_doc_freq(candidates, query_terms)

    # 归一化原始 cosine score
    raw_scores = [c.get("score", 0) for c in candidates]
    max_raw = max(raw_scores) if raw_scores else 1.0
    min_raw = min(raw_scores) if raw_scores else 0.0
    raw_range = max_raw - min_raw if max_raw != min_raw else 1.0

    scored = []
    for c in candidates:
        content = c.get("content", "")
        bm25 = _compute_bm25_score(query_terms, content, doc_count, doc_freq)
        cosine_raw = c.get("score", 0)
        cosine_norm = (cosine_raw - min_raw) / raw_range  # 归一化到 [0,1]
        hybrid = BM25_WEIGHT * bm25 + COSINE_WEIGHT * cosine_norm
        scored.append({**c, "rerank_score": round(hybrid, 4)})

    scored.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
    return scored[:top_k]


def _extract_terms(text):
    text = text.lower()
    chinese = re.findall(r'[\u4e00-\u9fff]+', text)
    terms = []
    for seg in chinese:
        for ch in seg:
            if ch not in STOPWORDS:
                terms.append(ch)
        for i in range(len(seg) - 1):
            bigram = seg[i:i+2]
            if not all(ch in STOPWORDS for ch in bigram):
                terms.append(bigram)
    english = re.findall(r'[a-z0-9]+', text)
    terms.extend(english)
    return terms


def _compute_doc_freq(candidates, query_terms):
    df = {}
    for term in query_terms:
        count = 0
        for c in candidates:
            content = c.get("content", "").lower()
            if term in content:
                count += 1
        df[term] = count
    return df


def _compute_bm25_score(query_terms, content, doc_count, doc_freq, k1=1.5, b=0.75):
    content_lower = content.lower()
    doc_len = len(content_lower)
    avg_dl = max(doc_len, 50)
    score = 0.0
    for term in set(query_terms):
        df = doc_freq.get(term, 0)
        if df == 0:
            idf = math.log((doc_count + 1) / 1.0)
        else:
            idf = math.log((doc_count - df + 0.5) / (df + 0.5) + 1)
        tf = content_lower.count(term)
        if tf == 0:
            continue
        tf_norm = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / avg_dl))
        score += idf * tf_norm

    # 归一化 BM25 分数到 [0, 1]
    max_possible = len(set(query_terms)) * math.log(doc_count + 1) * (k1 + 1) / (k1)
    if max_possible > 0:
        score = min(score / max_possible, 1.0)
    return score
