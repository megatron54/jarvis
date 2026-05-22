"""System control tool."""

import asyncio
import platform
import shutil
from typing import Any

from jarvis.tools.registry import BaseTool


# Allowed commands whitelist
SAFE_COMMANDS = [
    "echo", "date", "whoami", "hostname", "uname", "uptime", "df", "free",
    "ps", "top", "htop", "ls", "cat", "head", "tail", "wc", "find", "which",
    "python", "pip", "node", "npm", "git", "docker", "systemctl",
]

BLOCKED_COMMANDS = [
    "rm -rf /", "mkfs", "dd if=", ":(){ :|:& };:", "format",
    "shutdown", "reboot", "halt", "poweroff",
]


class SystemTool(BaseTool):
    name = "system"
    description = "Execute system commands, get system info, open applications"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["exec", "info", "open_app"],
                "description": "Action to perform",
            },
            "command": {"type": "string", "description": "Command to execute (for exec)"},
            "app": {"type": "string", "description": "Application to open (for open_app)"},
        },
        "required": ["action"],
    }
    permission_level = 2  # Dangerous - requires confirmation in production

    def _is_safe_command(self, cmd: str) -> bool:
        """Check if command is safe to execute."""
        cmd_lower = cmd.lower().strip()
        for blocked in BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                return False
        return True

    async def execute(self, **kwargs: Any) -> Any:
        action = kwargs.get("action")

        if action == "info":
            return {
                "platform": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python": platform.python_version(),
            }

        elif action == "exec":
            command = kwargs.get("command", "")
            if not self._is_safe_command(command):
                return {"error": "Command blocked for security reasons"}

            try:
                proc = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
                return {
                    "returncode": proc.returncode,
                    "stdout": stdout.decode(errors="replace")[:5000],
                    "stderr": stderr.decode(errors="replace")[:2000],
                }
            except asyncio.TimeoutError:
                return {"error": "Command timed out (30s)"}
            except Exception as e:
                return {"error": str(e)}

        elif action == "open_app":
            app = kwargs.get("app", "")
            app_path = shutil.which(app)
            if not app_path:
                return {"error": f"Application '{app}' not found"}
            try:
                await asyncio.create_subprocess_exec(app_path)
                return {"status": "opened", "app": app}
            except Exception as e:
                return {"error": str(e)}

        return {"error": f"Unknown action: {action}"}
