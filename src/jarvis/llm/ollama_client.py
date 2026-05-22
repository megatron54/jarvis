"""Ollama LLM client."""

from typing import AsyncGenerator

import httpx
import structlog

logger = structlog.get_logger()


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=120.0)

    async def health(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            resp = await self._client.get("/api/tags")
            return resp.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[dict]:
        """List available models."""
        resp = await self._client.get("/api/tags")
        resp.raise_for_status()
        return resp.json().get("models", [])

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        tools: list[dict] | None = None,
    ) -> dict:
        """Send a chat request and return the full response."""
        from jarvis.config import get_settings

        settings = get_settings()
        payload: dict = {
            "model": model or settings.default_model,
            "messages": messages,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools

        resp = await self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()

        result: dict = {"content": data.get("message", {}).get("content", "")}
        if data.get("message", {}).get("tool_calls"):
            result["tool_calls"] = data["message"]["tool_calls"]

        return result

    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream a chat response token by token."""
        from jarvis.config import get_settings

        settings = get_settings()
        payload = {
            "model": model or settings.default_model,
            "messages": messages,
            "stream": True,
        }

        async with self._client.stream("POST", "/api/chat", json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        """Generate embedding for text."""
        from jarvis.config import get_settings

        settings = get_settings()
        resp = await self._client.post(
            "/api/embed",
            json={"model": model or settings.embedding_model, "input": text},
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]

    async def close(self) -> None:
        await self._client.aclose()
