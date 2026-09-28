import uuid
import time
import logging
from typing import Optional
from pydantic import BaseModel, Field

from app.privacy.detector import PIIDetector, PrivacyEntity
from app.privacy.minimizer import QueryMinimizer

logger = logging.getLogger("notgoogle.privacy")
logger.setLevel(logging.INFO)


class PrivacyProcessResult(BaseModel):
    request_id: str
    original_length: int
    sanitized_content: str
    pii_detected: bool
    entities_detected: list[str]
    redaction_count: int
    persist_original: bool = False


class PrivacyAuditEntry(BaseModel):
    request_id: str
    operation: str
    pii_detected: bool
    entities_detected: list[str]
    redaction_count: int
    raw_content_stored: bool = False
    timestamp: float = Field(default_factory=time.time)


class PrivacyService:
    def __init__(self):
        self.detector = PIIDetector()
        self.minimizer = QueryMinimizer()

    def process_query(self, content: str, operation: str = "search") -> PrivacyProcessResult:

        request_id = f"req_{uuid.uuid4().hex[:10]}"
        

        entities: list[PrivacyEntity] = self.detector.detect(content)
        pii_detected = len(entities) > 0
        entity_types = sorted(list(set(e.type for e in entities)))


        redacted_text, redaction_count = self.detector.redact(content, entities=entities)


        minimized_text = self.minimizer.minimize(redacted_text)


        audit_entry = PrivacyAuditEntry(
            request_id=request_id,
            operation=operation,
            pii_detected=pii_detected,
            entities_detected=entity_types,
            redaction_count=redaction_count,
            raw_content_stored=False,
        )
        self._log_audit(audit_entry)


        return PrivacyProcessResult(
            request_id=request_id,
            original_length=len(content),
            sanitized_content=minimized_text,
            pii_detected=pii_detected,
            entities_detected=entity_types,
            redaction_count=redaction_count,
            persist_original=False,
        )

    def sanitize_context_for_llm(self, context_text: str) -> str:
        redacted_text, _ = self.detector.redact(context_text)
        return redacted_text

    @staticmethod
    def _log_audit(entry: PrivacyAuditEntry):

        logger.info(
            "[PRIVACY_AUDIT] req_id=%s op=%s pii=%s entities=%s redactions=%s raw_stored=%s",
            entry.request_id,
            entry.operation,
            entry.pii_detected,
            ",".join(entry.entities_detected) if entry.entities_detected else "NONE",
            entry.redaction_count,
            entry.raw_content_stored,
        )