import re
from typing import Optional
from pydantic import BaseModel, Field

class PrivacyEntity(BaseModel):
    type: str = Field(..., description="Entity classification tag (EMAIL, PHONE, API_KEY, etc.)")
    value: str = Field(..., description="Matched sensitive text (retained only ephemerally in-memory)")
    start: int = Field(..., ge=0, description="Start character offset")
    end: int = Field(..., ge=0, description="End character offset")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")


class PIIDetector:

    PATTERNS: dict[str, tuple[re.Pattern, str, float]] = {
        "OPENAI_KEY": (
            re.compile(r"\b(sk-[a-zA-Z0-9_-]{20,64})\b"),
            "[API_KEY]",
            0.99,
        ),
        "GITHUB_TOKEN": (
            re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,255})\b"),
            "[TOKEN]",
            0.99,
        ),
        "AWS_ACCESS_KEY": (
            re.compile(r"\b((?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16})\b"),
            "[API_KEY]",
            0.99,
        ),
        "JWT_BEARER": (
            re.compile(r"\b(?:Bearer\s+)?(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9._-]+\.[A-Za-z0-9._-]+)\b"),
            "[TOKEN]",
            0.98,
        ),
        "PASSWORD_ASSIGNMENT": (
            re.compile(r"""(?i)\b(?:password|passwd|pwd|secret)\s*(?:[:=]|\bis\b)\s*['"]?([^\s'"]{6,})['"]?"""),
            "[SECRET]",
            0.90,
        ),
        "URL_CREDENTIALS": (
            re.compile(r"https?://(?:[^:]+):([^@]+)@[a-zA-Z0-9.-]+"),
            "[URL_WITH_CREDENTIALS]",
            0.95,
        ),
        "CREDIT_CARD": (
            re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
            "[CREDIT_CARD]",
            0.95,
        ),
        "EMAIL": (
            re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
            "[EMAIL]",
            0.99,
        ),
        "PHONE": (
            re.compile(r"""(?x)
                (?:\+?\d{1,3}[-.\s]?)?
                (?:\(?\d{2,4}\)?[-.\s]?)?
                \d{3,5}[-.\s]?\d{4,5}
                \b
            """),
            "[PHONE]",
            0.85,
        ),
        "IPV4": (
            re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
            "[IP_ADDRESS]",
            0.95,
        ),
    }


    def detect(self, text: str) -> list[PrivacyEntity]:
        findings: list[PrivacyEntity] = []

        for entity_type, (regex, _, confidence) in self.PATTERNS.items():
            for match in regex.finditer(text):
                if match.groups() and match.group(1):
                    val = match.group(1)
                    start, end = match.span(1)
                else:
                    val = match.group(0)
                    start, end = match.span(0)

                findings.append(
                    PrivacyEntity(
                        type=entity_type,
                        value=val,
                        start=start,
                        end=end,
                        confidence=confidence,
                    )
                )

        return self._resolve_overlaps(findings)

    @staticmethod
    def _resolve_overlaps(entities: list[PrivacyEntity]) -> list[PrivacyEntity]:
        if not entities:
            return []
        sorted_entities = sorted(entities, key=lambda e: (e.start, -(e.end - e.start)))
        resolved: list[PrivacyEntity] = [sorted_entities[0]]

        for current in sorted_entities[1:]:
            prev = resolved[-1]
            if current.start < prev.end:
                if current.confidence > prev.confidence:
                    resolved[-1] = current
            else:
                resolved.append(current)

        return resolved

    def redact(self, text: str, entities: Optional[list[PrivacyEntity]] = None) -> tuple[str, int]:

        
        if entities is None:
            entities = self.detect(text)

        if not entities:
            return text, 0


        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)
        redacted = text
        redaction_count = 0

        for entity in sorted_entities:
            placeholder = self.PATTERNS.get(entity.type, (None, "[REDACTED]", 0.0))[1]
            redacted = redacted[:entity.start] + placeholder + redacted[entity.end:]
            redaction_count += 1

        return redacted, redaction_count