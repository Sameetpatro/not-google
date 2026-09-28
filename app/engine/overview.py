import os
import asyncio
from typing import Optional
import litellm
from dotenv import load_dotenv

from app.api.schemas import AIOverviewPayload, SearchItem
from app.engine.evidence import EvidenceEngine
from app.privacy.service import PrivacyService

load_dotenv()


class AIOverviewGenerator:
    SYSTEM_PROMPT = """You are an objective, precise AI search overview assistant.
Generate a concise, factual summary directly answering the user query based ONLY on the provided numbered sources.

Strict Rules:
1. Every claim must have an inline citation tag matching the source index, e.g. [1], [2].
2. Do not fabricate or assume facts not supported by the excerpts.
3. If the sources do not provide enough context to answer, state: "The retrieved documents do not contain enough information to fully answer this question."
4. Format with clean bullet points or short paragraphs."""

    def __init__(self, model_name: Optional[str] = None):
        # Configurable model: e.g., "groq/llama-3.3-70b-versatile", "gemini/gemini-1.5-flash", "gpt-4o-mini", or local "ollama/llama3"
        self.model = model_name or os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")
        self.evidence_engine = EvidenceEngine(max_sources=5)
        self.privacy_service = PrivacyService()

    async def generate_overview(
        self,
        query: str,
        local_results: Optional[list[SearchItem]] = None,
        web_results: Optional[list[SearchItem]] = None,
        local_result: Optional[list[SearchItem]] = None,
        web_result: Optional[list[SearchItem]] = None,
    ) -> Optional[AIOverviewPayload]:
        """
        Synthesizes an AI Overview answering the query based on retrieved local and web evidence.
        Returns None gracefully if no evidence is found or if the LLM provider fails.
        """
        effective_local = local_results if local_results is not None else (local_result or [])
        effective_web = web_results if web_results is not None else (web_result or [])

        evidence_text, citations = self.evidence_engine.compile_evidence(
            local_results=effective_local,
            web_results=effective_web,
        )
        if not citations or not evidence_text.strip():
            return None

        # BOUNDARY ENFORCEMENT: Scrub evidence context of any lingering PII before sending to external LLM
        safe_evidence = self.privacy_service.sanitize_context_for_llm(evidence_text)
        safe_query = self.privacy_service.sanitize_context_for_llm(query)

        user_content = (
            f"User Query: \"{safe_query}\"\n\n"
            f"Retrieved Sources:\n{safe_evidence}\n\n"
            "Provide an AI Overview answering the query using the sources above with inline citations [1], [2], etc."
        )

        for attempt in range(2):
            try:
                response = await litellm.acompletion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                    max_tokens=600,
                    timeout=20.0,
                )

                if not response.choices:
                    return None

                generated_text = (response.choices[0].message.content or "").strip()
                if not generated_text:
                    return None

                return AIOverviewPayload(
                    markdown_text=generated_text,
                    sources=citations,
                )

            except Exception as exc:
                if attempt == 0:
                    await asyncio.sleep(1.0)
                    continue
                print(f"[AIOverview] Generation error with model {self.model}: {exc}")
                return None
        return None
