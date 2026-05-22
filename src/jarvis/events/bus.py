"""Event bus using Redis Pub/Sub."""

from __future__ import annotations

import json
from typing import Any, Callable

import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class EventBus:
    """Simple event bus backed by Redis Pub/Sub."""

    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis: redis.Redis | None = None
        self._handlers: dict[str, list[Callable]] = {}

    async def initialize(self) -> None:
        self._redis = redis.from_url(self._redis_url, decode_responses=True)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    async def publish(self, event: str, data: dict[str, Any]) -> None:
        """Publish an event."""
        if self._redis:
            payload = json.dumps({"event": event, "data": data})
            await self._redis.publish(f"jarvis:{event}", payload)
            logger.debug("Event published", event=event)

    def on(self, event: str, handler: Callable) -> None:
        """Register an event handler."""
        self._handlers.setdefault(event, []).append(handler)
