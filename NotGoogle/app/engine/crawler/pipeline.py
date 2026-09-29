import asyncio
import logging
from typing import Optional, List
from urllib.parse import urlparse
import httpx

from app.api.schemas import ExtractedDocument
from app.engine.crawler.frontier import URLFrontier
from app.engine.crawler.extractor import DocumentExtractor
from app.engine.crawler.dedup import DocumentDeduplicator
from app.engine.crawler.storage import PostgresDocumentStore
from app.engine.indexer import InvertedIndex
from app.engine.vector_store import VectorSearchEngine
from app.engine.searxng import SearXNGClient

logger = logging.getLogger("notgoogle.crawler")
logger.setLevel(logging.INFO)

DEFAULT_SEEDS = [
    "https://fastapi.tiangolo.com/",
    "https://docs.python.org/3/tutorial/",
    "https://developer.mozilla.org/en-US/docs/Web",
    "https://en.wikipedia.org/wiki/Information_retrieval",
    "https://en.wikipedia.org/wiki/Search_engine",
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://en.wikipedia.org/wiki/World_Wide_Web",
    "https://en.wikipedia.org/wiki/Computer_science",
    "https://react.dev/",
    "https://nodejs.org/en/learn",
    "https://news.ycombinator.com/",
]


class ContinuousCrawler:
    """
    Continuous Crawler & Keyword Indexer.
    Continuously discovers, fetches, deduplicates, and indexes web content into
    both the BM25 Inverted Index and pgvector database.
    """

    def __init__(
        self,
        db_store: Optional[PostgresDocumentStore] = None,
        index: Optional[InvertedIndex] = None,
        vector_engine: Optional[VectorSearchEngine] = None,
        searxng_client: Optional[SearXNGClient] = None,
        politeness_delay: float = 0.5,
        user_agent: str = "NotGoogleBot/2.0 (+http://localhost:8000/bot)",
        timeout_seconds: float = 8.0,
        index_save_interval: int = 5,
    ):
        self.db_store = db_store or PostgresDocumentStore()
        self.index = index or InvertedIndex(index_file_path="search_index.pkl")
        self.vector_engine = vector_engine
        self.searxng_client = searxng_client or SearXNGClient()

        self.frontier = URLFrontier(politeness_delay=politeness_delay)
        self.dedup = DocumentDeduplicator(simhash_threshold=3)
        self.user_agent = user_agent
        self.timeout = timeout_seconds
        self.index_save_interval = index_save_interval

        self.is_running = False
        self.pages_crawled = 0
        self.pages_indexed = 0
        self.duplicates_skipped = 0
        self.errors_count = 0
        self._crawl_task: Optional[asyncio.Task] = None

    async def resume_from_db(self):
        """
        Hydrates frontier from PostgreSQL on server startup so the crawler
        resumes seamlessly without losing discovered links or re-fetching indexed pages.
        """
        try:
            seen_urls, outlinks = await self.db_store.get_all_crawled_urls_and_outlinks()
            self.frontier.seen_urls.update(seen_urls)
            self.pages_indexed = len(seen_urls)

            # Enqueue unvisited discovered outlinks
            added = 0
            for link in outlinks:
                if self.frontier.add_url(link):
                    added += 1

            if not self.frontier.queue:
                self.seed_urls(DEFAULT_SEEDS)

            print(
                f"[Crawler] Resumed from DB: {len(seen_urls)} crawled URLs marked as seen, "
                f"{len(self.frontier.queue)} pending frontier URLs ready to crawl."
            )
        except Exception as exc:
            print(f"[Crawler] Resume from DB notice: {exc}")

    def seed_urls(self, urls: List[str]) -> int:
        """Adds raw seed URLs to the crawl frontier."""
        added = self.frontier.add_seed_urls(urls)
        if added > 0:
            print(f"[Crawler] Added {added} seed URLs to frontier (Queue size: {len(self.frontier.queue)})")
        return added

    async def seed_by_keywords(self, keywords: List[str], max_per_keyword: int = 5) -> int:
        """
        Discovers authoritative starting seeds using the SearXNG web search client
        for the given keywords, expanding the search domain automatically.
        """
        total_added = 0
        for kw in keywords:
            try:
                results = await self.searxng_client.search(query=kw, limit=max_per_keyword)
                urls = [r.url for r in results if r.url]
                added = self.frontier.add_seed_urls(urls)
                total_added += added
                print(f"[Crawler] Seeded {added} URLs for keyword '{kw}'")
            except Exception as exc:
                print(f"[Crawler] Error discovering seeds for keyword '{kw}': {exc}")
        return total_added

    async def ingest_urls_now(self, urls: List[str], max_concurrent: int = 5):
        """
        Immediately fetches, extracts, deduplicates, and indexes a list of priority URLs
        (e.g. discovered during a user search), adding outlinks to the frontier.
        """
        if not urls:
            return
        headers = {"User-Agent": self.user_agent}
        async with httpx.AsyncClient(headers=headers) as client:
            tasks = [self._fetch_and_index_url(client, u) for u in urls[:max_concurrent]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            indexed_count = sum(
                1 for r in results if isinstance(r, dict) and r.get("status") == "indexed"
            )
            if indexed_count > 0:
                self.index.save_to_disk()
                print(f"[Crawler] Real-time query ingestion indexed {indexed_count} new pages! Total corpus: {self.index.total_docs}")

    async def _fetch_and_index_url(self, client: httpx.AsyncClient, url: str) -> Optional[dict]:
        """Fetches, extracts, deduplicates, and indexes a specific URL."""
        try:
            resp = await client.get(url, timeout=self.timeout, follow_redirects=True)
            content_type = resp.headers.get("content-type", "").lower()
            if resp.status_code != 200 or "text/html" not in content_type:
                return {"status": "skipped_non_html", "url": url}
            html = resp.text
        except Exception as exc:
            self.errors_count += 1
            return {"status": "fetch_error", "url": url, "error": str(exc)}

        self.pages_crawled += 1
        doc = DocumentExtractor.extract(url=url, html=html)
        if not doc:
            return {"status": "skipped_empty_content", "url": url}

        sha = DocumentDeduplicator.compute_sha256(doc.text_content)
        if await self.db_store.is_exact_duplicate(sha):
            self.duplicates_skipped += 1
            return {"status": "duplicate_skipped", "url": url}

        is_dup, reason = self.dedup.is_duplicate(doc)
        if is_dup:
            self.duplicates_skipped += 1
            return {"status": "near_duplicate_skipped", "url": url, "reason": reason}

        new_links = 0
        for link in doc.outlinks:
            if self.frontier.add_url(link):
                new_links += 1

        doc_id = await self.db_store.save_document(doc)
        doc_id_str = str(doc_id)
        self.index.add_document(
            doc_id=doc_id_str,
            title=doc.title,
            url=doc.url,
            snippet=doc.snippet,
            text_content=doc.text_content,
        )
        self.pages_indexed += 1
        await self.db_store.mark_as_indexed([doc_id])

        print(
            f"[Crawler #{self.pages_indexed}] Indexed: '{doc.title[:45]}' -> {url} "
            f"(+{new_links} links, Queue: {len(self.frontier.queue)})"
        )
        return {
            "status": "indexed",
            "doc_id": doc_id,
            "url": doc.url,
            "title": doc.title,
            "new_outlinks": new_links,
        }

    async def crawl_next(self, client: httpx.AsyncClient) -> Optional[dict]:
        """Fetches, extracts, deduplicates, and indexes a single document from the frontier."""
        url = await self.frontier.get_next_url_async()
        if not url:
            return None

        result = await self._fetch_and_index_url(client, url)

        # Periodic disk persistence of index
        if self.pages_indexed > 0 and self.pages_indexed % self.index_save_interval == 0:
            self.index.save_to_disk()
            if self.vector_engine:
                asyncio.create_task(self.vector_engine.generate_missing_embeddings(batch_size=5))

        return result

    async def run(self, max_pages: Optional[int] = None):
        """Main continuous crawling loop."""
        self.is_running = True
        if self.frontier.is_empty():
            self.seed_urls(DEFAULT_SEEDS)

        headers = {"User-Agent": self.user_agent}
        print(f"[Crawler] Engine started! Target pages: {max_pages or 'Continuous'}")

        async with httpx.AsyncClient(headers=headers) as client:
            consecutive_empty = 0
            while self.is_running:
                if max_pages and self.pages_indexed >= max_pages:
                    print(f"[Crawler] Reached target of {max_pages} pages. Stopping.")
                    break

                if self.frontier.is_empty():
                    consecutive_empty += 1
                    if consecutive_empty > 3:
                        print("[Crawler] Frontier queue empty, auto-replenishing with broad seeds...")
                        self.seed_urls(DEFAULT_SEEDS)
                        consecutive_empty = 0
                    await asyncio.sleep(2.0)
                    continue
                else:
                    consecutive_empty = 0

                try:
                    await self.crawl_next(client)
                except Exception as exc:
                    print(f"[Crawler] Error in crawl iteration: {exc}")
                    await asyncio.sleep(1.0)

        self.index.save_to_disk()
        self.is_running = False
        print(
            f"[Crawler] Completed run. Indexed: {self.pages_indexed}, "
            f"Duplicates: {self.duplicates_skipped}, Queue remaining: {len(self.frontier.queue)}"
        )

    def start_background(self, max_pages: Optional[int] = None):
        """Starts the continuous crawler loop in an asynchronous background task."""
        if self._crawl_task and not self._crawl_task.done():
            print("[Crawler] Background task already running.")
            return
        self._crawl_task = asyncio.create_task(self.run(max_pages=max_pages))

    def stop(self):
        """Signals the crawler loop to stop gracefully."""
        self.is_running = False
        if self._crawl_task and not self._crawl_task.done():
            self._crawl_task.cancel()
        print("[Crawler] Stop requested.")

    def get_stats(self) -> dict:
        """Returns live statistics of the crawler engine."""
        return {
            "is_running": self.is_running,
            "pages_crawled": self.pages_crawled,
            "pages_indexed": self.pages_indexed,
            "duplicates_skipped": self.duplicates_skipped,
            "errors_count": self.errors_count,
            "queue_size": len(self.frontier.queue),
            "total_seen_urls": self.frontier.total_seen(),
            "indexed_corpus_docs": self.index.total_docs,
        }


async def main_cli():
    import argparse

    parser = argparse.ArgumentParser(description="NotGoogle Continuous Crawler & Indexer")
    parser.add_argument("--keywords", type=str, help="Comma-separated keywords to discover seeds for")
    parser.add_argument("--seeds", type=str, help="Comma-separated initial seed URLs")
    parser.add_argument("--max-pages", type=int, default=15, help="Number of pages to crawl (default: 15)")
    parser.add_argument("--politeness", type=float, default=1.0, help="Politeness delay in seconds (default: 1.0)")
    args = parser.parse_args()

    db = PostgresDocumentStore()
    await db.connect()

    index = InvertedIndex(index_file_path="search_index.pkl")
    index.load_from_disk()

    v_engine = VectorSearchEngine(db_store=db)

    crawler = ContinuousCrawler(
        db_store=db,
        index=index,
        vector_engine=v_engine,
        politeness_delay=args.politeness,
    )

    if args.seeds:
        seed_list = [s.strip() for s in args.seeds.split(",") if s.strip()]
        crawler.seed_urls(seed_list)

    if args.keywords:
        kw_list = [k.strip() for k in args.keywords.split(",") if k.strip()]
        await crawler.seed_by_keywords(kw_list)

    await crawler.run(max_pages=args.max_pages)
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main_cli())
