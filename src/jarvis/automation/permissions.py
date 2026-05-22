"""Permission system for dangerous operations."""

from __future__ import annotations

from enum import IntEnum
from typing import Any

import structlog

logger = structlog.get_logger()


class PermissionLevel(IntEnum):
    SAFE = 0        # Auto-execute, no confirmation needed
    MODERATE = 1    # Execute with logging
    DANGEROUS = 2   # Requires user confirmation
    BLOCKED = 3     # Never execute


# Default permission rules
PERMISSION_RULES: dict[str, PermissionLevel] = {
    # File operations
    "files.read": PermissionLevel.SAFE,
    "files.list": PermissionLevel.SAFE,
    "files.write": PermissionLevel.MODERATE,
    "files.delete": PermissionLevel.DANGEROUS,

    # System operations
    "system.info": PermissionLevel.SAFE,
    "system.exec": PermissionLevel.DANGEROUS,
    "system.open_app": PermissionLevel.MODERATE,

    # Destructive operations
    "system.shutdown": PermissionLevel.BLOCKED,
    "system.format": PermissionLevel.BLOCKED,
    "system.rm_rf": PermissionLevel.BLOCKED,
}


class PermissionManager:
    """Manages permissions for tool execution."""

    def __init__(self):
        self._rules = PERMISSION_RULES.copy()
        self._overrides: dict[str, PermissionLevel] = {}
        self._pending_confirmations: dict[str, dict] = {}

    def check_permission(self, action: str) -> PermissionLevel:
        """Check the permission level for an action."""
        # Check overrides first
        if action in self._overrides:
            return self._overrides[action]
        # Check rules
        return self._rules.get(action, PermissionLevel.MODERATE)

    def can_execute(self, action: str) -> bool:
        """Check if an action can be executed without confirmation."""
        level = self.check_permission(action)
        return level < PermissionLevel.DANGEROUS

    def requires_confirmation(self, action: str) -> bool:
        """Check if an action needs user confirmation."""
        return self.check_permission(action) == PermissionLevel.DANGEROUS

    def is_blocked(self, action: str) -> bool:
        """Check if an action is permanently blocked."""
        return self.check_permission(action) >= PermissionLevel.BLOCKED

    def request_confirmation(self, action: str, params: dict[str, Any]) -> str:
        """Create a confirmation request. Returns request ID."""
        import uuid
        request_id = str(uuid.uuid4())[:8]
        self._pending_confirmations[request_id] = {
            "action": action,
            "params": params,
            "status": "pending",
        }
        logger.warning("Permission confirmation required", action=action, request_id=request_id)
        return request_id

    def confirm(self, request_id: str) -> dict | None:
        """Confirm a pending action. Returns the action details."""
        req = self._pending_confirmations.pop(request_id, None)
        if req:
            req["status"] = "confirmed"
            return req
        return None

    def deny(self, request_id: str) -> None:
        """Deny a pending action."""
        self._pending_confirmations.pop(request_id, None)
