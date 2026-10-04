import asyncio
import json
#import aioredis
from redis import asyncio as aioredis
from backend.fastapi_app.core.config import CacheConfig
from shared.utils.logger import get_logger

log = get_logger("ProgressBroadcastService")

cache_config = CacheConfig()

class ProgressBroadcastService:
    """
    Broadcaster for Celery task progress updates and live simulation streaming.
    Supports both Redis pub/sub (distributed) and in-memory queue fallback (local/dev).
    """

    def __init__(self, redis_url: str = cache_config.url + '2'):
        self.redis_url = redis_url
        self.redis = None
        self.is_connected = False
        self.in_memory_subscribers = {}  # {task_id: set of asyncio.Queue}

    async def connect(self):
        try:
            self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            self.is_connected = True
            log.info("Connected to Redis for progress broadcasting")
        except Exception as exc:
            self.redis = None
            self.is_connected = False
            log.warning(f"Redis unavailable for ProgressBroadcastService ({exc}). Using in-memory fallback.")

    async def disconnect(self):
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                pass
            self.is_connected = False

    async def publish(self, task_id: str, data: dict, channel_prefix: str = "task_progress"):
        """
        Publishes progress JSON to Redis pub/sub channel and any local in-memory subscribers.
        """
        message_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
        channel = f"{channel_prefix}:{task_id}"

        if self.is_connected and self.redis:
            try:
                await self.redis.publish(channel, message_str)
                log.debug(f"Published progress to Redis for {channel}: {data}")
            except Exception as e:
                log.warning(f"Failed to publish to Redis for {channel}: {e}")

        # Always notify in-memory subscribers (WebSocket listeners in this process)
        keys_to_notify = {channel, task_id}
        for k in keys_to_notify:
            if k in self.in_memory_subscribers:
                for q in list(self.in_memory_subscribers[k]):
                    try:
                        await q.put(message_str)
                    except Exception as e:
                        log.warning(f"Failed to dispatch to in-memory queue: {e}")

    async def publish_batch(self, batch_id: str, data: dict):
        """
        Publishes batch-level progress JSON to the batch Redis pub/sub channel.
        """
        await self.publish(batch_id, data, channel_prefix="batch_progress")

    async def subscribe(self, task_id: str, channel_prefix: str = "task_progress"):
        """
        Creates an async generator yielding progress updates for a task or batch.
        Uses Redis pub/sub if available, otherwise falls back to local in-memory queue.
        """
        channel = f"{channel_prefix}:{task_id}"
        if self.is_connected and self.redis:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)
            log.info(f"Subscribed to Redis channel: {channel}")

            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        yield message["data"]
            finally:
                try:
                    await pubsub.unsubscribe(channel)
                    await pubsub.close()
                except Exception:
                    pass
                log.info(f"Unsubscribed from Redis channel {channel}")
        else:
            # In-memory queue fallback
            queue = asyncio.Queue()
            if channel not in self.in_memory_subscribers:
                self.in_memory_subscribers[channel] = set()
            self.in_memory_subscribers[channel].add(queue)
            log.info(f"Subscribed to in-memory channel {channel}")

            try:
                while True:
                    data = await queue.get()
                    yield data
            finally:
                if channel in self.in_memory_subscribers:
                    self.in_memory_subscribers[channel].discard(queue)
                    if not self.in_memory_subscribers[channel]:
                        del self.in_memory_subscribers[channel]
                log.info(f"Unsubscribed from in-memory channel {channel}")

    async def subscribe_batch(self, batch_id: str):
        """
        Creates an async generator yielding progress updates for a batch.
        """
        async for msg in self.subscribe(batch_id, channel_prefix="batch_progress"):
            yield msg


_shared_broadcast_service = None

def get_broadcast_service() -> ProgressBroadcastService:
    global _shared_broadcast_service
    if _shared_broadcast_service is None:
        _shared_broadcast_service = ProgressBroadcastService()
    return _shared_broadcast_service
