import re

class QueryMinimizer:
    PREAMBLE_PATTERNS = [
        re.compile(r"""(?i)^(?:hello|hi|hey|greetings|dear\s+ai|please\s+help\s+me)\b[,\s.-]*"""),
        re.compile(r"""(?i)\b(?:my\s+name\s+is|i\s+am|i'm)\s+[^,.!?]+\b[,\s.-]*"""),
        re.compile(r"""(?i)\b(?:i\s+am|i'm)\s+\d{1,3}\s*(?:years\s+old|yo)\b[,\s.-]*"""),
        re.compile(r"""(?i)\b(?:i\s+live\s+in|from|located\s+in)\s+[A-Z][a-zA-Z\s]+[,\s.-]*"""),
        re.compile(r"""(?i)\b(?:i\s+study|student\s+at|working\s+at)\s+[^,.!?]+[,\s.-]*"""),
        re.compile(r"""(?i)\b(?:as\s+a\s+matter\s+of\s+fact|can\s+you\s+tell\s+me|i\s+wanted\s+to\s+ask)\b[,\s.-]*"""),
    ]

    INTENT_MARKERS = [
        re.compile(r"""(?i)\b(which|what|how|why|when|where|who|explain|compare|build|optimize|design|find)\b.*"""),
        re.compile(r"""(?i)\b(?:best|difference\s+between|guide\s+for|tutorial)\b.*"""),
    ]

    @classmethod
    def minimise(cls, text:str) ->str:

        cleaned = text.strip()

        for pattern in cls.PREAMBLE_PATTERNS:
            cleaned = pattern.sub("", cleaned).strip()

        sentences = re.split(r"[.!?]\s+", cleaned)
        actionable_clauses = []

        for sentence in sentences:
            trimmed = sentence.strip()
            if not trimmed:
                continue
            if any(marker.search(trimmed) for marker in cls.INTENT_MARKERS):
                actionable_clauses.append(trimmed)

        if actionable_clauses:
            minimized = " ".join(actionable_clauses).strip()

            if len(minimized) >= 10:
                return minimized

        return cleaned if len(cleaned) >= 5 else text

    # Alias for US/UK spelling compatibility
    minimize = minimise