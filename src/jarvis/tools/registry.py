"""Tool registry and base class."""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger()


class BaseTool(ABC):
    """Base class for all Jarvis tools."""

    name: str
    description: str
    parameters: dict  # JSON Schema
    permission_level: int = 0  # 0=safe, 1=moderate, 2=dangerous, 3=blocked

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with given parameters."""
        ...

    def get_schema(self) -> dict:
        """Get the tool schema for LLM function calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info("Tool registered", tool=tool.name)

    def discover(self) -> None:
        """Auto-discover and register built-in tools."""
        from jarvis.tools.datetime_tool import DateTimeTool
        from jarvis.tools.notes import NotesTool
        from jarvis.tools.tasks import TasksTool
        from jarvis.tools.files import FilesTool
        from jarvis.tools.system import SystemTool

        for tool_class in [DateTimeTool, NotesTool, TasksTool, FilesTool, SystemTool]:
            self.register(tool_class())

    def get_schemas(self) -> list[dict]:
        """Get all tool schemas for LLM."""
        return [tool.get_schema() for tool in self._tools.values()]

    async def execute(self, tool_name: str, params: dict) -> Any:
        """Execute a tool by name."""
        tool = self._tools.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}

        if tool.permission_level >= 3:
            return {"error": f"Tool '{tool_name}' is blocked for security"}

        try:
            result = await tool.execute(**params)
            logger.info("Tool executed", tool=tool_name, success=True)
            return result
        except Exception as e:
            logger.error("Tool execution failed", tool=tool_name, error=str(e))
            return {"error": str(e)}

    async def execute_batch(self, tool_calls: list[dict]) -> list[Any]:
        """Execute multiple tool calls."""
        results = []
        for call in tool_calls:
            func = call.get("function", {})
            name = func.get("name", "")
            args = func.get("arguments", {})
            if isinstance(args, str):
                import json
                args = json.loads(args)
            result = await self.execute(name, args)
            results.append(result)
        return results
