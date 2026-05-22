"""DateTime tool."""

from datetime import datetime
from typing import Any

from jarvis.tools.registry import BaseTool


class DateTimeTool(BaseTool):
    name = "get_datetime"
    description = "Get the current date and time"
    parameters = {"type": "object", "properties": {}, "required": []}
    permission_level = 0

    async def execute(self, **kwargs: Any) -> dict:
        now = datetime.now()
        return {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "iso": now.isoformat(),
        }
