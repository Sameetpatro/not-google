from app.privacy.detector import PIIDetector
from app.privacy.minimizer import QueryMinimizer
from app.privacy.service import PrivacyService


def test_pii_detection():
    detector = PIIDetector()

    sample = (
        "My email is sameet@example.com and phone is +91 98765 43210. "
        "Server IP is 192.168.1.50 and token is sk-abcdef1234567890abcdef1234567890."
    )

    entities = detector.detect(sample)
    types = {e.type for e in entities}

    assert "EMAIL" in types, "Failed to detect email"
    assert "PHONE" in types, "Failed to detect phone"
    assert "IPV4" in types, "Failed to detect IP"
    assert "OPENAI_KEY" in types, "Failed to detect API key"

    print("✔ [1/5] PII Detection Passed")


def test_pii_redaction():
    detector = PIIDetector()
    raw = "Contact sameet@example.com or visit 10.0.0.1 for details."
    redacted, count = detector.redact(raw)

    assert "sameet@example.com" not in redacted
    assert "10.0.0.1" not in redacted
    assert "[EMAIL]" in redacted
    assert "[IP_ADDRESS]" in redacted
    assert count == 2

    print("✔ [2/5] PII Redaction Passed")


def test_data_minimization():
    minimizer = QueryMinimizer()
    raw = "Hi, my name is Sameet. I am 21 years old and I study CSE. Which database should I use for a Go backend?"
    minimized = minimizer.minimize(raw)

    assert "Sameet" not in minimized
    assert "21" not in minimized
    assert "Which database should I use for a Go backend?" in minimized

    print("✔ [3/5] Query Minimization Passed")


def test_audit_logging_safety():
    service = PrivacyService()
    sensitive_input = "My secret password is secretpassword123 and key is sk-123456789012345678901234567890."

    result = service.process_query(sensitive_input, operation="test_op")

    # Verify return object doesn't leak original
    assert result.persist_original is False
    assert "secretpassword123" not in result.sanitized_content
    assert "sk-1234567890" not in result.sanitized_content

    print("✔ [4/5] Privacy-Safe Logging & Ephemeral Context Passed")


def test_leakage_scanner():
    """
    Simulates external service dispatches (SearXNG / LLM context)
    and verifies that known raw sensitive tokens never appear in the payload.
    """
    service = PrivacyService()

    known_leaks = [
        "john.doe@notgoogle.com",
        "+1 555-0199",
        "sk-testkey12345678901234567890",
        "192.168.0.100",
    ]

    dirty_query = (
        f"Hey, I am at 192.168.0.100. Reach me at john.doe@notgoogle.com or call +1 555-0199. "
        f"API key is sk-testkey12345678901234567890. How to configure PostgreSQL connection pooling?"
    )

    result = service.process_query(dirty_query, operation="external_dispatch")
    external_payload = result.sanitized_content

    # Leakage Scanner assertion
    for leak in known_leaks:
        assert leak not in external_payload, f"LEAK DETECTED: {leak} survived sanitization!"

    assert "How to configure PostgreSQL connection pooling?" in external_payload

    print("✔ [5/5] External Boundary Leakage Scanner Passed: 0 Leaks Detected")


if __name__ == "__main__":
    print("\n=== Running NotGoogle Privacy Engine Test Suite ===\n")
    test_pii_detection()
    test_pii_redaction()
    test_data_minimization()
    test_audit_logging_safety()
    test_leakage_scanner()
    print("\nAll Privacy Tests Passed Successfully.")
