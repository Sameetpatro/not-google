import os
import hashlib
from typing import Optional
import httpx
from dotenv import load_dotenv

from app.api.schemas import SearchItem

load_dotenv()

class SearXNGClient:
    def __init__(self, base_url: Optional[str] = None, timeout_second: float = 5.0): 
        self.base_url = (base_url or os.getenv("SEARXNG_URL") or "http://localhost:8080").rstrip("/")
        self.timeout = timeout_second
        self.timeout_second = timeout_second

    def _build_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
        }

    async def search(self, query: str, limit: int = 10) -> list[SearchItem]:

        params = {
            "q": query,
            "format": "json",
            "engines": "google,bing,duckduckgo",
            "language": "en",
        }

        headers = self._build_headers()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    headers=headers,
                )

                if response.status_code != 200:
                    print(f"[SearXNG] Non-200 HTTP code ({response.status_code}) from {self.base_url}")
                    return []

                data = response.json()
                results = data.get("results", [])

                items: list[SearchItem] = []
                for idx, entry in enumerate(results[:limit]):
                    url = entry.get("url", "")
                    if not url:
                        continue

                    doc_id = hashlib.md5(url.encode("utf-8")).hexdigest()[:12]
                    raw_score = entry.get("score")
                    score = (
                        float(raw_score)
                        if raw_score is not None
                        else round(1.0 - (idx * 0.05), 4)
                    )

                    items.append(
                        SearchItem(
                            id=f"sx_{doc_id}",
                            title=entry.get("title", "No Title"),
                            url=url,
                            snippet=entry.get("content", ""),
                            score=round(score, 4),
                            source=f"searxng_{entry.get('engine', 'web')}",
                        )
                    )
                return items

        except httpx.TimeoutException:
            print(f"[SearXNG] Connection timed out after {self.timeout}s to {self.base_url}")
            return []
        except httpx.RequestError as exc:
            print(f"[SearXNG] Network error querying {self.base_url}: {exc}")
            return []
        except Exception as exc:
            print(f"[SearXNG] Unexpected error parsing response: {exc}")
            return []
