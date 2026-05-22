"""Semantic memory using ChromaDB for RAG."""

from __future__ import annotations

import uuid
from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


class SemanticMemory:
    """Vector-based semantic memory using ChromaDB for RAG retrieval."""

    def __init__(self, chroma_url: str, ollama_base_url: str, embedding_model: str):
        self._chroma_url = chroma_url.rstrip("/")
        self._ollama_url = ollama_base_url.rstrip("/")
        self._embedding_model = embedding_model
        self._client = httpx.AsyncClient(base_url=self._chroma_url, timeout=30.0)
        self._ollama = httpx.AsyncClient(base_url=self._ollama_url, timeout=60.0)
        self._collection_id: str | None = None

    async def initialize(self) -> None:
        """Ensure the default collection exists."""
        try:
            # Create or get collection
            resp = await self._client.post(
                "/api/v1/collections",
                json={"name": "jarvis_knowledge", "metadata": {"hnsw:space": "cosine"}},
            )
            if resp.status_code in (200, 201):
                self._collection_id = resp.json()["id"]
            else:
                # Collection might already exist, try to get it
                resp = await self._client.get("/api/v1/collections/jarvis_knowledge")
                if resp.status_code == 200:
                    self._collection_id = resp.json()["id"]
            logger.info("Semantic memory initialized", collection_id=self._collection_id)
        except Exception as e:
            logger.warning("ChromaDB not available, semantic memory disabled", error=str(e))

    async def _embed(self, text: str) -> list[float]:
        """Generate embedding using Ollama."""
        resp = await self._ollama.post(
            "/api/embed",
            json={"model": self._embedding_model, "input": text},
        )
        resp.raise_for_status()
        return resp.json()["embeddings"][0]

    async def add(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
        doc_id: str | None = None,
    ) -> str:
        """Add a document to semantic memory."""
        if not self._collection_id:
            return ""

        doc_id = doc_id or str(uuid.uuid4())
        embedding = await self._embed(content)

        await self._client.post(
            f"/api/v1/collections/{self._collection_id}/add",
            json={
                "ids": [doc_id],
                "embeddings": [embedding],
                "documents": [content],
                "metadatas": [metadata or {}],
            },
        )
        logger.debug("Document added to semantic memory", doc_id=doc_id)
        return doc_id

    async def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Search for relevant documents."""
        if not self._collection_id:
            return []

        query_embedding = await self._embed(query)

        resp = await self._client.post(
            f"/api/v1/collections/{self._collection_id}/query",
            json={
                "query_embeddings": [query_embedding],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"],
            },
        )

        if resp.status_code != 200:
            return []

        data = resp.json()
        results = []
        if data.get("documents") and data["documents"][0]:
            for i, doc in enumerate(data["documents"][0]):
                results.append({
                    "content": doc,
                    "metadata": data["metadatas"][0][i] if data.get("metadatas") else {},
                    "distance": data["distances"][0][i] if data.get("distances") else 0,
                })

        return results

    async def add_conversation_summary(self, session_id: str, summary: str) -> None:
        """Store a conversation summary for long-term retrieval."""
        await self.add(
            content=summary,
            metadata={"type": "conversation_summary", "session_id": session_id},
        )

    async def add_note(self, note_id: str, title: str, content: str, tags: list[str]) -> None:
        """Index a note for semantic search."""
        await self.add(
            content=f"{title}\n\n{content}",
            metadata={"type": "note", "note_id": note_id, "tags": ",".join(tags)},
            doc_id=f"note_{note_id}",
        )

    async def close(self) -> None:
        await self._client.aclose()
        await self._ollama.aclose()
