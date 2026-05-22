"""System control and automation."""

from __future__ import annotations

import asyncio
import platform
from typing import Any

import structlog

logger = structlog.get_logger()


class SystemControl:
    """Control the local operating system."""

    def __init__(self):
        self._platform = platform.system().lower()

    async def open_application(self, app_name: str) -> dict:
        """Open an application by name."""
        commands = {
            "linux": f"xdg-open {app_name} || {app_name} &",
            "windows": f"start {app_name}",
            "darwin": f"open -a {app_name}",
        }
        cmd = commands.get(self._platform, app_name)

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        return {"status": "opened", "app": app_name}

    async def get_active_window(self) -> dict:
        """Get info about the currently active window."""
        if self._platform == "linux":
            proc = await asyncio.create_subprocess_shell(
                "xdotool getactivewindow getwindowname",
                stdout=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return {"window": stdout.decode().strip()}
        return {"window": "unknown (unsupported platform)"}

    async def set_clipboard(self, text: str) -> dict:
        """Set clipboard content."""
        if self._platform == "linux":
            proc = await asyncio.create_subprocess_shell(
                "xclip -selection clipboard",
                stdin=asyncio.subprocess.PIPE,
            )
            await proc.communicate(input=text.encode())
        elif self._platform == "windows":
            proc = await asyncio.create_subprocess_shell(
                f'echo {text}| clip',
                stdin=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
        return {"status": "copied"}

    async def get_clipboard(self) -> str:
        """Get clipboard content."""
        if self._platform == "linux":
            proc = await asyncio.create_subprocess_shell(
                "xclip -selection clipboard -o",
                stdout=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            return stdout.decode()
        return ""

    async def send_notification(self, title: str, message: str) -> dict:
        """Send a desktop notification."""
        if self._platform == "linux":
            await asyncio.create_subprocess_shell(
                f'notify-send "{title}" "{message}"'
            )
        elif self._platform == "windows":
            # PowerShell notification
            script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $textNodes = $template.GetElementsByTagName("text")
            $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}"))
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}"))
            '''
            # Simplified fallback
            await asyncio.create_subprocess_shell(
                f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show(\'{message}\', \'{title}\')"'
            )
        return {"status": "sent", "title": title}

    async def run_script(self, script_path: str, timeout: int = 60) -> dict:
        """Run a script file with timeout."""
        try:
            proc = await asyncio.create_subprocess_shell(
                f"bash {script_path}" if self._platform == "linux" else script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "returncode": proc.returncode,
                "stdout": stdout.decode(errors="replace")[:5000],
                "stderr": stderr.decode(errors="replace")[:2000],
            }
        except asyncio.TimeoutError:
            proc.kill()
            return {"error": f"Script timed out after {timeout}s"}
