"""Base connector class for external integrations."""

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger()


class ConnectorResult:
    """Result from a connector operation."""

    def __init__(self, success: bool, data: Any = None, error: str | None = None):
        self.success = success
        self.data = data
        self.error = error

    def to_dict(self) -> dict:
        return {"success": self.success, "data": self.data, "error": self.error}


class BaseConnector(ABC):
    """Base class for all external service connectors."""

    name: str
    description: str
    requires_auth: bool = True

    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the service."""
        ...

    @abstractmethod
    async def execute(self, action: str, params: dict[str, Any]) -> ConnectorResult:
        """Execute an action on the service."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the service is reachable."""
        ...

    async def disconnect(self) -> None:
        """Cleanup connections."""
        pass
