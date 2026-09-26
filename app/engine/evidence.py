from typing import Optional
from app.api.schemas import SearchItem, CitationSource

class EvidenceEngine:
    def __init__(self, max_sources: int = 5, max_char_per_sources: int = 400):
        self.max_sources = max_sources
        self.max_chars_per_source = max_char_per_sources

    def compile_evidence(
        self,
        local_results: list[SearchItem],
        web_results: Optional[list[SearchItem]] = None,
    ) -> tuple[str, list[CitationSource]]:
        
        combined: list[SearchItem] = []
        seen_urls: set[str] = set()

        pool = list(local_results[: self.max_sources])
        if web_results:
            pool.extend(web_results[: self.max_sources])

        for item in pool:
            if item.url not in seen_urls and item.snippet.strip():
                seen_urls.add(item.url)
                combined.append(item)
            if len(combined) >= self.max_sources:
                break

        citations: list[CitationSource] = []
        evidence_blocks: list[str] = []

        for idx, item in enumerate(combined, start=1):
            truncated_snippet = item.snippet[: self.max_chars_per_source].strip()

            citations.append(
                CitationSource(
                    citation_id=idx,
                    title=item.title,
                    url=item.url,
                    snippet=truncated_snippet,
                )
            )

            evidence_blocks.append(
                f"[{idx}] Title: {item.title}\nURL: {item.url}\nExcerpt: {truncated_snippet}"
            )

        evidence_text = "\n\n".join(evidence_blocks)
        return evidence_text, citations