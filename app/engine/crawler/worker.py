import asyncio
import httpx
from typing import Optional
from app.engine.crawler.message_bus import RabbitMQBus, ConsumedTask


class CrawlerWorker:
    def __init__(
        self,
        message_bus: RabbitMQBus,
        worker_id: str = "worker-1",
        user_agent: str = "NotGoogleBot/1.0 (+http://localhost:8000/bot)",
        timeout_seconds: float = 10.0,
        prefetch_count: int = 5,
    ):
        self.message_bus = message_bus
        self.worker_id = worker_id
        self.user_agent = user_agent
        self.timeout = timeout_seconds
        self.prefetch_count = prefetch_count
        self.is_running = False

    async def fetch(self, client: httpx.AsyncClient, url: str) -> tuple[Optional[str], int]:
        try:
            response = await client.get(url, timeout=self.timeout, follow_redirects=True)
            content_type = response.headers.get("content-type", "").lower()
            if response.status_code == 200 and "text/html" in content_type:
                return response.text, response.status_code
            return None, response.status_code
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            print(f"[{self.worker_id}] Transient network issue fetching {url}: {exc}")
            raise
        except Exception as exc:
            print(f"[{self.worker_id}] Non-recoverable error fetching {url}: {exc}")
            return None, 0

    async def run(self):
        self.is_running = True
        headers = {"User-Agent": self.user_agent}
        async with httpx.AsyncClient(headers=headers) as client:
            print(f"[{self.worker_id}] Worker started. Listening for tasks...")
            async for task in self.message_bus.consume_tasks(prefetch_count=self.prefetch_count):
                if not self.is_running:
                    await task.reject(requeue=True)
                    break

                url = task.data.get("url")
                depth = task.data.get("depth", 0)
                print(f"[{self.worker_id}] Fetching (depth={depth}): {url}")

                try:
                    html, status_code = await self.fetch(client, url)
                    if html:
                        await self.message_bus.publish_raw_html(
                            url=url, html=html, status_code=status_code
                        )
                        print(f"[{self.worker_id}] Published {len(html)} bytes to raw_html for {url}")
                    else:
                        print(f"[{self.worker_id}] Skipped (empty or non-HTML, code {status_code}): {url}")

                    await task.ack()

                except (httpx.ConnectError, httpx.TimeoutException):
                    print(f"[{self.worker_id}] Requeuing URL due to network timeout: {url}")
                    await task.reject(requeue=True)

                except Exception as exc:
                    print(f"[{self.worker_id}] Permanent task failure ({exc}). Discarding: {url}")
                    await task.reject(requeue=False)

    def stop(self):
        self.is_running = False