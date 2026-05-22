"""Memory management system."""

from __future__ import annotations

import json
from typing import Any

import httpx
import redis.asyncio as redis
import structlog

logger = structlog.get_logger()


class MemoryManager:
    """Manages short-term (Redis), long-term (PostgreSQL), and semantic (ChromaDB) memory."""

    def __init__(self, redis_url: str, database_url: str, chroma_url: str):
        self._redis_url = redis_url
        self._database_url = database_url
        self._chroma_url = chroma_url
        self._redis: redis.Redis | None = None
        self._chroma_client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize memory backends."""
        self._redis = redis.from_url(self._redis_url, decode_responses=True)
        self._chroma_client = httpx.AsyncClient(base_url=self._chroma_url, timeout=30.0)
        logger.info("Memory manager initialized")

    async def close(self) -> None:
        """Close all connections."""
        if self._redis:
            await self._redis.aclose()
        if self._chroma_client:
            await self._chroma_client.aclose()

    async def health(self) -> bool:
        """Check memory backends health."""
        try:
            if self._redis:
                await self._redis.ping()
                return True
        except Exception:
            pass
        return False

    # --- Conversation Memory (Redis) ---

    async def get_conversation(self, session_id: str) -> list[dict]:
        """Get conversation history for a session."""
        if not self._redis:
            return []
        data = await self._redis.get(f"conv:{session_id}")
        if data:
            return json.loads(data)
        return []

    async def save_conversation(self, session_id: str, messages: list[dict]) -> None:
        """Save conversation history. Keep last 50 messages."""
        if not self._redis:
            return
        # Keep only last 50 messages to manage context window
        trimmed = messages[-50:]
        await self._redis.set(
            f"conv:{session_id}",
            json.dumps(trimmed),
            ex=86400 * 7,  # 7 days TTL
        )

    async def clear_conversation(self, session_id: str) -> None:
        """Clear conversation history."""
        if self._redis:
            await self._redis.delete(f"conv:{session_id}")

    # --- User Preferences ---

    async def get_user_preferences(self) -> dict[str, Any]:
        """Get stored user preferences."""
        if not self._redis:
            return {}
        data = await self._redis.get("user:preferences")
        if data:
            return json.loads(data)
        return {}

    async def set_user_preferences(self, prefs: dict[str, Any]) -> None:
        """Update user preferences."""
        if not self._redis:
            return
        existing = await self.get_user_preferences()
        existing.update(prefs)
        await self._redis.set("user:preferences", json.dumps(existing))

    # --- Notes ---

    async def save_note(self, title: str, content: str, tags: list[str] | None = None) -> str:
        """Save a note."""
        import uuid

        note_id = str(uuid.uuid4())[:8]
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "tags": tags or [],
        }
        if self._redis:
            await self._redis.hset("notes", note_id, json.dumps(note))
        return note_id

    async def get_notes(self, query: str | None = None) -> list[dict]:
        """Get all notes, optionally filtered."""
        if not self._redis:
            return []
        all_notes = await self._redis.hgetall("notes")
        notes = [json.loads(v) for v in all_notes.values()]
        if query:
            query_lower = query.lower()
            notes = [
                n for n in notes
                if query_lower in n["title"].lower() or query_lower in n["content"].lower()
            ]
        return notes

    # --- Tasks ---

    async def save_task(self, title: str, priority: str = "medium") -> str:
        """Save a task."""
        import uuid

        task_id = str(uuid.uuid4())[:8]
        task = {
            "id": task_id,
            "title": title,
            "priority": priority,
            "status": "pending",
        }
        if self._redis:
            await self._redis.hset("tasks", task_id, json.dumps(task))
        return task_id

    async def get_tasks(self, status: str | None = None) -> list[dict]:
        """Get all tasks."""
        if not self._redis:
            return []
        all_tasks = await self._redis.hgetall("tasks")
        tasks = [json.loads(v) for v in all_tasks.values()]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        return tasks

    async def update_task(self, task_id: str, **kwargs: Any) -> bool:
        """Update a task."""
        if not self._redis:
            return False
        data = await self._redis.hget("tasks", task_id)
        if not data:
            return False
        task = json.loads(data)
        task.update(kwargs)
        await self._redis.hset("tasks", task_id, json.dumps(task))
        return True
