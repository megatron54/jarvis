"""File management tool."""

import os
from pathlib import Path
from typing import Any

from jarvis.tools.registry import BaseTool


# Restricted paths that cannot be accessed
BLOCKED_PATHS = ["/etc", "/boot", "/sys", "/proc", "C:\\Windows\\System32"]


class FilesTool(BaseTool):
    name = "files"
    description = "List, read, create, and search files on the local filesystem"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "read", "write", "search", "info"],
                "description": "Action to perform",
            },
            "path": {"type": "string", "description": "File or directory path"},
            "content": {"type": "string", "description": "Content to write (for write action)"},
            "query": {"type": "string", "description": "Search pattern (for search action)"},
        },
        "required": ["action", "path"],
    }
    permission_level = 1  # Moderate - logs all operations

    def _is_safe_path(self, path: str) -> bool:
        """Check if path is allowed."""
        abs_path = str(Path(path).resolve())
        return not any(abs_path.startswith(blocked) for blocked in BLOCKED_PATHS)

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action")
        path = kwargs.get("path", "")

        if not self._is_safe_path(path):
            return {"error": "Access to this path is restricted"}

        try:
            if action == "list":
                p = Path(path)
                if not p.exists():
                    return {"error": "Path does not exist"}
                entries = []
                for item in p.iterdir():
                    entries.append({
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    })
                return {"path": str(p), "entries": entries[:100]}

            elif action == "read":
                p = Path(path)
                if not p.is_file():
                    return {"error": "Not a file or does not exist"}
                if p.stat().st_size > 100_000:
                    return {"error": "File too large (>100KB)"}
                content = p.read_text(encoding="utf-8", errors="replace")
                return {"path": str(p), "content": content[:10000]}

            elif action == "write":
                p = Path(path)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(kwargs.get("content", ""), encoding="utf-8")
                return {"status": "written", "path": str(p)}

            elif action == "info":
                p = Path(path)
                if not p.exists():
                    return {"error": "Path does not exist"}
                stat = p.stat()
                return {
                    "path": str(p),
                    "size": stat.st_size,
                    "is_file": p.is_file(),
                    "is_dir": p.is_dir(),
                    "modified": stat.st_mtime,
                }

            elif action == "search":
                p = Path(path)
                query = kwargs.get("query", "")
                matches = []
                for item in p.rglob(f"*{query}*"):
                    matches.append(str(item))
                    if len(matches) >= 20:
                        break
                return {"matches": matches}

            return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}
