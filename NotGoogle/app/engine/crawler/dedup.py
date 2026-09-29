import hashlib
import re
from typing import Optional
from app.api.schemas import ExtractedDocument

class DocumentDeduplicator:
    def __init__(self, simhash_threshold: int = 3):
        self.simhash_threshold = simhash_threshold
        self.exact_hashes: set[str] = set()
        self.simhashes: list[tuple[str, int]] = []

    @staticmethod
    def compute_sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _token_hash(token: str) -> int:
        return int(hashlib.md5(token.encode("utf-8")).hexdigest()[:16], 16)

    @classmethod
    def compute_simhash(cls, text: str) -> int:

        #find all tokens
        tokens = re.findall(r"\w+", text.lower())
        if not tokens:
            return 0

        #break token if more than 3 into 3-word token
        if len(tokens) >= 3:
            shingles = [" ".join(tokens[i : i + 3]) for i in range(len(tokens) - 2)]
        else:
            shingles = tokens

        #voting wala logic, find the most relatable or not relatable word phase 
        v = [0] * 64
        for shingle in shingles:
            t_hash = cls._token_hash(shingle)
            for i in range(64):
                bit = (t_hash >> i) & 1
                if bit == 1:
                    v[i] += 1
                else:
                    v[i] -= 1

        #return whose v[i] > 0 ("or" ops for all)
        fingerprint = 0
        for i in range(64):
            if v[i] > 0:
                fingerprint |= (1 << i)

        return fingerprint

    @staticmethod
    def hamming_distance(h1: int, h2: int) -> int:
        return (h1 ^ h2).bit_count()


    def is_duplicate(self, doc: ExtractedDocument) -> tuple[bool, Optional[str]]:
        #checks if the document is exact duplicate or near duplicate

        #tier1 similarity check
        sha = self.compute_sha256(doc.text_content)
        if sha in self.exact_hashes:
            return True, "Exact match"

        #tier2
        doc_simhash = self.compute_simhash(doc.text_content)
        for existing_url, existing_simhash in self.simhashes:
            dist = self.hamming_distance(doc_simhash, existing_simhash)
            if dist <= self.simhash_threshold:
                return True, f"near_duplicate_of:{existing_url} (dist={dist})"

        #if not same, save it
        self.exact_hashes.add(sha)
        self.simhashes.append((doc.url, doc_simhash))
        return False, None



#testing
def test_deduplication():
    dedup = DocumentDeduplicator(simhash_threshold=3)

    # 1. Original Document
    doc1 = ExtractedDocument(
        url="https://example.com/python-guide",
        title="Python Guide",
        snippet="A complete guide to Python language",
        text_content="Python is an interpreted high-level general-purpose programming language. Created by Guido van Rossum and first released in 1991.",
        outlinks=[],
        content_length=135,
    )

    is_dup, reason = dedup.is_duplicate(doc1)
    print(f"Doc 1 [Original]: is_dup={is_dup}, reason={reason}")

    # 2. Exact Duplicate (Different URL, identical text)
    doc2 = ExtractedDocument(
        url="https://mirror.com/python-guide",
        title="Mirror Python Guide",
        snippet="A complete guide to Python language",
        text_content="Python is an interpreted high-level general-purpose programming language. Created by Guido van Rossum and first released in 1991.",
        outlinks=[],
        content_length=135,
    )

    is_dup, reason = dedup.is_duplicate(doc2)
    print(f"Doc 2 [Mirror / Exact]: is_dup={is_dup}, reason={reason}")

    # 3. Near-Duplicate (Only tiny timestamps/words modified)
    doc3 = ExtractedDocument(
        url="https://blog.com/python-repost",
        title="Python Guide Repost",
        snippet="A complete guide to Python language",
        text_content="Python is an interpreted high-level general-purpose programming language. Created by Guido van Rossum and first released in 1991. Updated today at 12:00 PM.",
        outlinks=[],
        content_length=165,
    )

    is_dup, reason = dedup.is_duplicate(doc3)
    print(f"Doc 3 [Near-Duplicate]: is_dup={is_dup}, reason={reason}")

    # 4. Completely Unique Document
    doc4 = ExtractedDocument(
        url="https://example.com/fastapi-guide",
        title="FastAPI Guide",
        snippet="FastAPI is a modern web framework",
        text_content="FastAPI is a modern, fast high-performance web framework for building APIs with Python based on standard Python type hints.",
        outlinks=[],
        content_length=130,
    )

    is_dup, reason = dedup.is_duplicate(doc4)
    print(f"Doc 4 [Unique Document]: is_dup={is_dup}, reason={reason}")


if __name__ == "__main__":
    test_deduplication()

