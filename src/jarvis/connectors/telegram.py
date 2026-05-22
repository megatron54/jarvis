"""Telegram bot connector."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from jarvis.connectors.base import BaseConnector, ConnectorResult

logger = structlog.get_logger()


class TelegramConnector(BaseConnector):
    """Connector for Telegram Bot API."""

    name = "telegram"
    description = "Send and receive messages via Telegram"
    requires_auth = True

    def __init__(self, bot_token: str):
        self._token = bot_token
        self._base_url = f"https://api.telegram.org/bot{bot_token}"
        self._client = httpx.AsyncClient(timeout=30.0)

    async def authenticate(self) -> bool:
        try:
            resp = await self._client.get(f"{self._base_url}/getMe")
            return resp.status_code == 200
        except Exception:
            return False

    async def health_check(self) -> bool:
        return await self.authenticate()

    async def execute(self, action: str, params: dict[str, Any]) -> ConnectorResult:
        try:
            if action == "send_message":
                resp = await self._client.post(
                    f"{self._base_url}/sendMessage",
                    json={
                        "chat_id": params["chat_id"],
                        "text": params["text"],
                        "parse_mode": params.get("parse_mode", "Markdown"),
                    },
                )
                resp.raise_for_status()
                return ConnectorResult(success=True, data=resp.json())

            elif action == "get_updates":
                resp = await self._client.get(
                    f"{self._base_url}/getUpdates",
                    params={"offset": params.get("offset", 0), "timeout": 10},
                )
                resp.raise_for_status()
                return ConnectorResult(success=True, data=resp.json().get("result", []))

            return ConnectorResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def disconnect(self) -> None:
        await self._client.aclose()
