import re
from app.api.schemas import ProcessedQuery

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for",
    "if", "in", "into", "is", "it", "no", "not", "of", "on", "or",
    "such", "that", "the", "their", "then", "there", "these",
    "they", "this", "to", "was", "will", "with"
}

QUESTION_STARTERS = {
    "what", "why", "how", "when", "where", "who", "which",
    "can", "could", "should", "is", "are", "do", "does"
}

class QueryProcessor:
    @staticmethod
    def clean_text(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def process_text(cls, text: str) -> ProcessedQuery:
        text = text.lower().strip()

        first_word = text.lower().split()[0] if text else ""
        is_question = text.endswith("?") or first_word in QUESTION_STARTERS

        normalized = cls.clean_text(text)
        tokens = normalized.split() if normalized else []

        filtered_tokens = [t for t in tokens if t not in STOP_WORDS]

        if not filtered_tokens and tokens:
            filtered_tokens = tokens

        return ProcessedQuery(
            raw_query=text,
            normalized_query=normalized,
            tokens=tokens,
            filtered_tokens=filtered_tokens,
            is_question=is_question,
        )





