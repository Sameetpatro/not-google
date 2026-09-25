import math
from typing import Optional
from sentence_transformers import CrossEncoder

from app.api.schemas import SearchItem

class DocumentReranker:
    MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    def __init__(self):
        self.model: Optional[str] = None

    def _get_model(self) -> CrossEncoder:
        if self.model is None:
            print("[Reranker] Loading Cross-Encoder model (ms-marco-MiniLM-L-6-v2)...")
            self.model = CrossEncoder(self.MODEL_NAME)
        return self.model

    @staticmethod
    def _sigmoid(x: float) -> float:
        try:
            return 1.0 / (1.0 + math.exp(-x))
        except OverflowError:
            return 0.0 if x < 0 else 1.0

    _get_sigmoid = _sigmoid

    def rerank(self,
        query: str,
        candidates: list[SearchItem],
        top_k: int = 10,
    ) -> list[SearchItem]:
        if not candidates:
            return []

        model = self._get_model()


        #make pair for query,document 
        pairs = [] 
        for item in candidates:

            doc_context = f"{item.title}. {item.snippet}"
            pairs.append([query, doc_context])

        raw_scores = model.predict(pairs)

        reranked_items: list[SearchItem] = []
        for item, score in zip(candidates, raw_scores):
            normalized_score = self._sigmoid(float(score))
            reranked_items.append(
                SearchItem(
                    id=item.id,
                    title=item.title,
                    url=item.url,
                    snippet=item.snippet,
                    score=round(normalized_score, 4),
                    source="cross_encoder",
                )
            )

        reranked_items.sort(key=lambda x: x.score, reverse=True)

        return reranked_items[:top_k]
