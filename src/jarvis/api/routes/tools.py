"""Tools management endpoints."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/tools")
async def list_tools(request: Request) -> dict:
    """List all available tools."""
    registry = request.app.state.tools
    return {"tools": registry.get_schemas()}


@router.post("/tools/{tool_name}/execute")
async def execute_tool(request: Request, tool_name: str, params: dict) -> dict:
    """Execute a specific tool directly."""
    registry = request.app.state.tools
    result = await registry.execute(tool_name, params)
    return {"result": result}
