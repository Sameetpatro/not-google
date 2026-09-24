import math
from collections import defaultdict
from typing import Optional

from app.api.schemas import SearchItem
from app.engine.indexer import InvertedIndex

class BM25Ranker:
    def __init__(self, index: InvertedIndex, k1: float = 1.5, b: float = 0.75):
        self.index = index
        self.k1 = k1
        self.b = b

    
    def compute_idf(self, term: str) -> float:
        doc_freq = self.index.get_doc_freq(term)
        total_docs = self.index.total_docs

        if total_docs == 0 or doc_freq == 0:
            return 0.0

        return math.log(1.0 + (total_docs - doc_freq + 0.5) / (doc_freq + 0.5))

    def score_candidates(self, query_tokens: list[str]) -> dict[str, float]:
        if not query_tokens or self.index.total_docs == 0:
            return {}

        scores: dict[str, float] = defaultdict(float)
        avg_doc_len = self.index.avg_doc_len or 1.0

        for token in query_tokens:
            postings = self.index.get_postings(token)
            if not postings:
                continue

            idf = self.compute_idf(token)

            for posting in postings:
                doc_id = posting.doc_id
                tf = posting.term_freq
                doc_meta = self.index.doc_store.get(doc_id)
                if not doc_meta:
                    continue
                doc_len = doc_meta.length

                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avg_doc_len))
                term_score = idf * (numerator / denominator)

                scores[doc_id] += term_score

        return scores

    def search(self, query_tokens: list[str], top_k: int = 20) -> list[SearchItem]:

        raw_scores = self.score_candidates(query_tokens)
        if not raw_scores:
            return []

        ranked_doc_ids = sorted(raw_scores.keys(), key=lambda did: raw_scores[did], reverse=True)[:top_k]

        results: list[SearchItem] = []
        for did in ranked_doc_ids:
            meta = self.index.doc_store[did]
            results.append(
                SearchItem(
                    id=meta.doc_id,
                    title=meta.title,
                    url=meta.url,
                    snippet=meta.snippet,
                    score=round(raw_scores[did], 4),
                    source="local_bm25",
                )
            )

        return results
