import asyncio
import json
#import aioredis
from redis import asyncio as aioredis
from shared.utils.logger import get_logger

log = get_logger("ProgressBroadcastService")

class ProgressBroadcastService:
    """
    Redis-based broadcaster for Celery task progress updates.
    Allows multiple clients to subscribe to a single task’s progress channel.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/2"):
        self.redis_url = redis_url
        self.subscribers = {}  # {task_id: set(websocket_or_queue)}

    async def connect(self):
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        log.info("Connected to Redis for progress broadcasting")

    async def publish(self, task_id: str, data: dict):
        """
        Called when Celery reports progress.
        Publishes progress JSON to Redis pub/sub channel.
        """
        channel = f"task_progress:{task_id}"
        await self.redis.publish(channel, json.dumps(data))
        log.debug(f"Published progress for {task_id}: {data}")

    async def subscribe(self, task_id: str):
        """
        Creates an async generator that yields progress updates for a task.
        """
        pubsub = self.redis.pubsub()
        channel = f"task_progress:{task_id}"
        await pubsub.subscribe(channel)
        log.info(f"Subscribed to Redis channel: {channel}")

        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield message["data"]
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            log.info(f"Unsubscribed from {channel}")
