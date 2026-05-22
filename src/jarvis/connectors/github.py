"""GitHub connector."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from jarvis.connectors.base import BaseConnector, ConnectorResult

logger = structlog.get_logger()


class GitHubConnector(BaseConnector):
    """Connector for GitHub API."""

    name = "github"
    description = "Interact with GitHub repositories, issues, and PRs"
    requires_auth = True

    def __init__(self, token: str):
        self._token = token
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=30.0,
        )

    async def authenticate(self) -> bool:
        try:
            resp = await self._client.get("/user")
            return resp.status_code == 200
        except Exception:
            return False

    async def health_check(self) -> bool:
        return await self.authenticate()

    async def execute(self, action: str, params: dict[str, Any]) -> ConnectorResult:
        try:
            if action == "list_repos":
                resp = await self._client.get("/user/repos", params={"per_page": 30})
                resp.raise_for_status()
                repos = [{"name": r["full_name"], "url": r["html_url"]} for r in resp.json()]
                return ConnectorResult(success=True, data=repos)

            elif action == "list_issues":
                repo = params["repo"]
                resp = await self._client.get(f"/repos/{repo}/issues")
                resp.raise_for_status()
                return ConnectorResult(success=True, data=resp.json())

            elif action == "create_issue":
                repo = params["repo"]
                resp = await self._client.post(
                    f"/repos/{repo}/issues",
                    json={"title": params["title"], "body": params.get("body", "")},
                )
                resp.raise_for_status()
                return ConnectorResult(success=True, data=resp.json())

            return ConnectorResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def disconnect(self) -> None:
        await self._client.aclose()
