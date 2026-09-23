import json
import asyncio
from typing import Optional, AsyncGenerator, Any
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import Message, DeliveryMode
from aio_pika.abc import (
    AbstractRobustConnection,
    AbstractRobustChannel,
    AbstractIncomingMessage,
    AbstractQueue,
)

class ConsumedTask:
    def __init__(self, data: dict, raw_message: Optional[AbstractIncomingMessage] = None):
        self.data = data
        self._raw_message = raw_message

    async def ack(self):
        if self._raw_message:
            await self._raw_message.ack()

    async def reject(self, requeue: bool = True):
        if self._raw_message:
            await self._raw_message.reject(requeue=requeue)


class RabbitMQBus:
    QUEUE_TASKS = "crawler_tasks"
    QUEUE_RAW_HTML = "raw_html"

    def __init__(self, amqp_url: str = "amqp://guest:guest@localhost:5672/"):
        self.amqp_url = amqp_url
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractRobustChannel] = None
        self.is_connected = False

        #fallback for RabbitMQ when RabbitMQ is not available
        self._fallback_queues: dict[str, asyncio.Queue] = {
            self.QUEUE_TASKS: asyncio.Queue(),
            self.QUEUE_RAW_HTML: asyncio.Queue(),
        }

    async def start(self):
        try:
            self.connection = await aio_pika.connect_robust(self.amqp_url)
            self.channel = await self.connection.channel()

            await self.channel.declare_queue(self.QUEUE_TASKS, durable=True)
            await self.channel.declare_queue(self.QUEUE_RAW_HTML, durable=True)

            self.is_connected = True
            print(f"[RabbitMQBus] Connected to RabbitMQ at {self.amqp_url}")

        except Exception as exc:
            self.is_connected = False
            print(f"[RabbitMQBus] Broker unreachable ({exc}). Running in in-memory fallback mode.")

    async def stop(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def publish(self, queue_name: str, payload: dict[str, Any]):
        if self.is_connected and self.channel:
            body = json.dumps(payload).encode("utf-8")
            message = Message(
                body=body,
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json",
            )
            await self.channel.default_exchange.publish(message, routing_key=queue_name)
        else:
            queue = self._fallback_queues.setdefault(queue_name, asyncio.Queue())
            await queue.put(payload)

    async def publish_task(self, url: str, depth: int = 0):
        await self.publish(self.QUEUE_TASKS, {"url": url, "depth": depth})

    async def publish_raw_html(self, url: str, html: str, status_code: int):
        await self.publish(
            self.QUEUE_RAW_HTML,
            {
                "url": url,
                "html": html,
                "status_code": status_code,
            },
        )

    async def consume_tasks(
        self, prefetch_count: int = 10
    ) -> AsyncGenerator[ConsumedTask, None]:
        if self.is_connected and self.channel:
            await self.channel.set_qos(prefetch_count=prefetch_count)
            queue: AbstractQueue = await self.channel.get_queue(self.QUEUE_TASKS)

            async with queue.iterator() as queue_iter:
                message: AbstractIncomingMessage
                async for message in queue_iter:
                    try:
                        data = json.loads(message.body.decode("utf-8"))
                        yield ConsumedTask(data=data, raw_message=message)
                    except Exception as err:
                        print(f"[RabbitMQBus] Malformed task discarded: {err}")
                        await message.reject(requeue=False)
        else:
            queue = self._fallback_queues[self.QUEUE_TASKS]
            while True:
                data = await queue.get()
                yield ConsumedTask(data=data, raw_message=None)
                queue.task_done()