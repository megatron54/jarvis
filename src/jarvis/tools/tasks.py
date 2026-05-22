"""Tasks management tool."""

from typing import Any

from jarvis.tools.registry import BaseTool


class TasksTool(BaseTool):
    name = "tasks"
    description = "Manage TODO tasks: create, list, complete, delete"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "list", "complete", "delete"],
                "description": "Action to perform",
            },
            "title": {"type": "string", "description": "Task title (for create)"},
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Task priority",
            },
            "task_id": {"type": "string", "description": "Task ID (for complete/delete)"},
            "status": {"type": "string", "description": "Filter by status (for list)"},
        },
        "required": ["action"],
    }
    permission_level = 0

    async def execute(self, **kwargs: Any) -> Any:
        from jarvis.config import get_settings
        from jarvis.memory.manager import MemoryManager

        settings = get_settings()
        memory = MemoryManager(
            redis_url=settings.redis_url,
            database_url=settings.database_url,
            chroma_url=settings.chroma_url,
        )
        await memory.initialize()

        try:
            action = kwargs.get("action")
            if action == "create":
                task_id = await memory.save_task(
                    title=kwargs.get("title", "Untitled"),
                    priority=kwargs.get("priority", "medium"),
                )
                return {"status": "created", "id": task_id}
            elif action == "list":
                tasks = await memory.get_tasks(status=kwargs.get("status"))
                return {"tasks": tasks}
            elif action == "complete":
                ok = await memory.update_task(kwargs["task_id"], status="completed")
                return {"status": "completed" if ok else "not_found"}
            elif action == "delete":
                ok = await memory.update_task(kwargs["task_id"], status="deleted")
                return {"status": "deleted" if ok else "not_found"}
            else:
                return {"error": f"Unknown action: {action}"}
        finally:
            await memory.close()
