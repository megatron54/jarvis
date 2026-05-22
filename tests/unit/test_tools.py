"""Tests for Jarvis tools."""

import pytest
from jarvis.tools.datetime_tool import DateTimeTool
from jarvis.tools.files import FilesTool
from jarvis.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_datetime_tool():
    tool = DateTimeTool()
    result = await tool.execute()
    assert "date" in result
    assert "time" in result
    assert "day_of_week" in result


@pytest.mark.asyncio
async def test_files_tool_blocked_path():
    tool = FilesTool()
    result = await tool.execute(action="read", path="/etc/shadow")
    assert "error" in result
    assert "restricted" in result["error"]


def test_tool_registry():
    registry = ToolRegistry()
    registry.discover()
    schemas = registry.get_schemas()
    assert len(schemas) >= 5
    names = [s["function"]["name"] for s in schemas]
    assert "get_datetime" in names
    assert "notes" in names
    assert "tasks" in names
    assert "files" in names
    assert "system" in names
