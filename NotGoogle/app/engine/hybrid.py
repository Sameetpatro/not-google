from collections import defaultdict
from typing import Optional

from app.api.schemas import SearchItem, ProcessedQuery
from app.engine.bm25 import BM25Ranker
from app.engine.vector_store import VectorSearchEngine

class HybridRetriever:
    def __init__(self, bm25_ranker: BM25Ranker, vector_engine: VectorSearchEngine, rrf_k: int = 60):
        self.bm25 = bm25_ranker
        self.vector = vector_engine
        self.rrf_k = rrf_k

    async def search(self, query: ProcessedQuery, candidate_pool_size: int = 25, top_k: int = 10) -> list[SearchItem]:
        bm25_results = self.bm25.search(
            query_tokens=query.filtered_tokens,
            top_k=candidate_pool_size,
        )
        vector_results = await self.vector.search(
            query_text=query.normalized_query,
            top_k=candidate_pool_size,
        )

        rrf_scores: dict[str, float] = defaultdict(float)
        doc_registry: dict[str, SearchItem] = {}

        for rank, item in enumerate(bm25_results, start=1):
            doc_id = item.id
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank)
            if doc_id not in doc_registry:
                doc_registry[doc_id] = item

        for rank, item in enumerate(vector_results, start=1):
            doc_id = item.id
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank)
            if doc_id not in doc_registry:
                doc_registry[doc_id] = item


        sorted_ids = sorted(
            rrf_scores.keys(), key=lambda did: rrf_scores[did], reverse=True
        )[:top_k]

        final_results: list[SearchItem] = []
        for did in sorted_ids:
            original_item = doc_registry[did]
            final_results.append(
                SearchItem(
                    id=original_item.id,
                    title=original_item.title,
                    url=original_item.url,
                    snippet=original_item.snippet,
                    score=round(rrf_scores[did], 6),
                    source="hybrid_rrf",
                )
            )

        return final_results


HybridRetriver = HybridRetriever