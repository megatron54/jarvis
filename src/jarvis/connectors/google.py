"""Google Calendar and Gmail connector."""

from __future__ import annotations

from typing import Any

import structlog

from jarvis.connectors.base import BaseConnector, ConnectorResult

logger = structlog.get_logger()


class GoogleConnector(BaseConnector):
    """Connector for Google APIs (Calendar + Gmail).
    
    Requires OAuth2 credentials. Setup:
    1. Create project in Google Cloud Console
    2. Enable Calendar API and Gmail API
    3. Create OAuth2 credentials (Desktop app)
    4. Download credentials.json
    5. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env
    """

    name = "google"
    description = "Interact with Google Calendar and Gmail"
    requires_auth = True

    def __init__(self, client_id: str, client_secret: str, token_path: str = ".google_token.json"):
        self._client_id = client_id
        self._client_secret = client_secret
        self._token_path = token_path
        self._credentials: Any = None

    async def authenticate(self) -> bool:
        """Authenticate using OAuth2 flow."""
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            from pathlib import Path
            import json

            token_file = Path(self._token_path)
            if token_file.exists():
                creds_data = json.loads(token_file.read_text())
                self._credentials = Credentials.from_authorized_user_info(creds_data)
                if self._credentials.expired and self._credentials.refresh_token:
                    self._credentials.refresh(Request())
                    token_file.write_text(self._credentials.to_json())
                return self._credentials.valid

            # Need to run OAuth flow (interactive)
            logger.warning("Google OAuth: No token found. Run 'jarvis google-auth' to authenticate.")
            return False

        except ImportError:
            logger.error("google-auth not installed: pip install google-auth google-auth-oauthlib google-api-python-client")
            return False
        except Exception as e:
            logger.error("Google auth failed", error=str(e))
            return False

    async def health_check(self) -> bool:
        return self._credentials is not None and self._credentials.valid

    async def execute(self, action: str, params: dict[str, Any]) -> ConnectorResult:
        if not self._credentials:
            return ConnectorResult(success=False, error="Not authenticated")

        try:
            if action == "list_events":
                return await self._list_events(params)
            elif action == "create_event":
                return await self._create_event(params)
            elif action == "list_emails":
                return await self._list_emails(params)
            elif action == "send_email":
                return await self._send_email(params)
            return ConnectorResult(success=False, error=f"Unknown action: {action}")
        except Exception as e:
            return ConnectorResult(success=False, error=str(e))

    async def _list_events(self, params: dict) -> ConnectorResult:
        from googleapiclient.discovery import build
        service = build("calendar", "v3", credentials=self._credentials)
        
        events_result = service.events().list(
            calendarId="primary",
            maxResults=params.get("max_results", 10),
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for event in events_result.get("items", []):
            events.append({
                "summary": event.get("summary", ""),
                "start": event.get("start", {}).get("dateTime", event.get("start", {}).get("date")),
                "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date")),
            })

        return ConnectorResult(success=True, data=events)

    async def _create_event(self, params: dict) -> ConnectorResult:
        from googleapiclient.discovery import build
        service = build("calendar", "v3", credentials=self._credentials)

        event = {
            "summary": params["title"],
            "start": {"dateTime": params["start"], "timeZone": params.get("timezone", "UTC")},
            "end": {"dateTime": params["end"], "timeZone": params.get("timezone", "UTC")},
            "description": params.get("description", ""),
        }

        created = service.events().insert(calendarId="primary", body=event).execute()
        return ConnectorResult(success=True, data={"id": created["id"], "link": created.get("htmlLink")})

    async def _list_emails(self, params: dict) -> ConnectorResult:
        from googleapiclient.discovery import build
        service = build("gmail", "v1", credentials=self._credentials)

        results = service.users().messages().list(
            userId="me",
            maxResults=params.get("max_results", 10),
            q=params.get("query", "is:unread"),
        ).execute()

        messages = []
        for msg in results.get("messages", [])[:5]:
            detail = service.users().messages().get(userId="me", id=msg["id"], format="metadata").execute()
            headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
            messages.append({
                "id": msg["id"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "date": headers.get("Date", ""),
            })

        return ConnectorResult(success=True, data=messages)

    async def _send_email(self, params: dict) -> ConnectorResult:
        from googleapiclient.discovery import build
        import base64
        from email.mime.text import MIMEText

        service = build("gmail", "v1", credentials=self._credentials)

        message = MIMEText(params["body"])
        message["to"] = params["to"]
        message["subject"] = params["subject"]
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return ConnectorResult(success=True, data={"id": sent["id"]})
