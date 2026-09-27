from typing import Optional
from app.api.schemas import SearchItem, CitationSource


class EvidenceEngine:
    def __init__(
        self,
        max_sources: int = 5,
        max_chars_per_source: int = 400,
        max_char_per_sources: Optional[int] = None,
    ):
        self.max_sources = max_sources
        self.max_chars_per_source = (
            max_char_per_sources if max_char_per_sources is not None else max_chars_per_source
        )

    def compile_evidence(
        self,
        local_results: list[SearchItem],
        web_results: Optional[list[SearchItem]] = None,
    ) -> tuple[str, list[CitationSource]]:
        """
        Deduplicates and compiles local and web search results into an evidence prompt block
        and a structured citation list for LLM synthesis.
        Interleaves top local and web results to prevent local results from starving web results.
        """
        combined: list[SearchItem] = []
        seen_urls: set[str] = set()

        clean_local = [
            item for item in local_results
            if item.snippet and item.snippet.strip()
        ]
        clean_web = [
            item for item in (web_results or [])
            if item.snippet and item.snippet.strip()
        ]

        max_len = max(len(clean_local), len(clean_web)) if (clean_local or clean_web) else 0
        pool: list[SearchItem] = []
        for i in range(max_len):
            if i < len(clean_local):
                pool.append(clean_local[i])
            if i < len(clean_web):
                pool.append(clean_web[i])

        for item in pool:

            canonical_url = item.url.rstrip("/")
            if canonical_url not in seen_urls:
                seen_urls.add(canonical_url)
                combined.append(item)
            if len(combined) >= self.max_sources:
                break

        citations: list[CitationSource] = []
        evidence_blocks: list[str] = []

        for idx, item in enumerate(combined, start=1):
            raw_snippet = item.snippet.strip()
            if len(raw_snippet) > self.max_chars_per_source:
                truncated_snippet = raw_snippet[: self.max_chars_per_source].rstrip() + "..."
            else:
                truncated_snippet = raw_snippet

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