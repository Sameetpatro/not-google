import time
import asyncio
from collections import deque
from urllib.parse import urlparse, urlunparse, urldefrag
from typing import Optional

class URLFrontier:
    def __init__(self, politeness_delay: float = 1.0):
        self.politeness_delay = politeness_delay
        self.queue: deque[str] = deque()
        self.seen_urls: set[str] = set()
        self.host_last_crawled: dict[str, float] = {}

    @staticmethod
    def canonicalize_url(raw_url: str) -> Optional[str]:
        try:
            defragged, _ = urldefrag(raw_url.strip())
            parsed = urlparse(defragged)

            if parsed.scheme not in ("http", "https"):
                return None

            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()

            if netloc.endswith(":80") and scheme == "http":
                netloc = netloc[:-3]
            elif netloc.endswith(":443") and scheme == "https":
                netloc = netloc[:-4]

            path = parsed.path or "/"
            if len(path) > 1 and path.endswith("/"):
                path = path[:-1]

            normalized = urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
            return normalized

        except Exception:
            return None

    def add_url(self, url: str) -> bool:
        canonical = self.canonicalize_url(url)
        if not canonical:
            return False
        if canonical in self.seen_urls:
            return False
        self.seen_urls.add(canonical)
        self.queue.append(canonical)
        return True

    def add_seed_urls(self, seeds: list[str]) -> int:
        added = 0
        for seed in seeds:
            if self.add_url(seed):
                added+=1

        return added

    def is_empty(self) -> bool:
        return len(self.queue) == 0
    
    def total_seen(self) -> int :
        return len(self.seen_urls)

    def get_next_url(self) -> Optional[str]:
        if not self.queue:
            return None

        checked_count = 0
        queue_len = len(self.queue)

        while checked_count < queue_len:
            url = self.queue.popleft()
            host = urlparse(url).netloc
            now = time.time()
            last_time = self.host_last_crawled.get(host, 0.0)

            if now - last_time >= self.politeness_delay:
                self.host_last_crawled[host] = now
                return url
            else:
                self.queue.append(url)
                checked_count += 1

        url = self.queue.popleft()
        host = urlparse(url).netloc
        now = time.time()
        last_time = self.host_last_crawled.get(host, 0.0)
        time_to_wait = self.politeness_delay - (now - last_time)
        
        if time_to_wait > 0:
            time.sleep(time_to_wait)
            
        self.host_last_crawled[host] = time.time()
        return url

    async def get_next_url_async(self) -> Optional[str]:
        if not self.queue:
            return None

        checked_count = 0
        queue_len = len(self.queue)

        while checked_count < queue_len:
            url = self.queue.popleft()
            host = urlparse(url).netloc
            now = time.time()
            last_time = self.host_last_crawled.get(host, 0.0)

            if now - last_time >= self.politeness_delay:
                self.host_last_crawled[host] = now
                return url
            else:
                self.queue.append(url)
                checked_count += 1

        url = self.queue.popleft()
        host = urlparse(url).netloc
        now = time.time()
        last_time = self.host_last_crawled.get(host, 0.0)
        time_to_wait = self.politeness_delay - (now - last_time)

        if time_to_wait > 0:
            await asyncio.sleep(time_to_wait)

        self.host_last_crawled[host] = time.time()
        return url