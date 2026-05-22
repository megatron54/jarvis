"""Notion API connector."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from jarvis.connectors.base import BaseConnector, ConnectorResult

logger = structlog.get_logger()


class NotionConnector(BaseConnector):
    """Connector for Notion API."""

    name = "notion"
    description = "Read and write Notion pages and databases"
    requires_auth = True

    def __init__(self, api_key: str):
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            base_url="https://api.notion.com/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def authenticate(self) -> bool:
        try:
            resp = await self._client.get("/users/me")
            return resp.status_code == 200
        except Exception:
            return False

    async def health_check(self) -> bool:
        return await self.authenticate()

    async def execute(self, action: str, params: dict[str, Any]) -> ConnectorResult:
        try:
            if action == "search":
                resp = await self._client.post("/search", json={
                    "query": params.get("query", ""),
                    "page_size": params.get("limit", 10),
                })
                resp.raise_for_status()
                results = resp.json().get("results", [])
                pages = [{"id": r["id"], "title": self._extract_title(r)} for r in results]
                return ConnectorResult(success=True, data=pages)

            elif action == "get_page":
                resp = await self._client.get(f"/pages/{params['page_id']}")
                resp.raise_for_status()
                return ConnectorResult(success=True, data=resp.json())

            elif action == "create_page":
                body = {
                    "parent": {"database_id": params["database_id"]},
                    "properties": params.get("properties", {}),
                    "children": params.get("children", []),
                }
                resp = await self._client.post("/pages", json=body)
                resp.raise_for_status()
                return ConnectorResult(success=True, data=resp.json())

            return ConnectorResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    def _extract_title(self, page: dict) -> str:
        """Extract title from a Notion page object."""
        props = page.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title":
                title_arr = prop.get("title", [])
                if title_arr:
                    return title_arr[0].get("plain_text", "")
        return "Untitled"

    async def disconnect(self) -> None:
        await self._client.aclose()
