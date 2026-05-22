"""Notes management tool."""

from typing import Any

from jarvis.tools.registry import BaseTool


class NotesTool(BaseTool):
    name = "notes"
    description = "Create, list, and search personal notes"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["create", "list", "search"],
                "description": "Action to perform",
            },
            "title": {"type": "string", "description": "Note title (for create)"},
            "content": {"type": "string", "description": "Note content (for create)"},
            "query": {"type": "string", "description": "Search query (for search)"},
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for the note",
            },
        },
        "required": ["action"],
    }
    permission_level = 0

    async def execute(self, **kwargs: Any) -> Any:
        # Import here to avoid circular deps in registry
        from jarvis.config import get_settings
        from jarvis.memory.manager import MemoryManager

        # In production this would use the app's memory instance
        # For now, create a lightweight connection
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
                note_id = await memory.save_note(
                    title=kwargs.get("title", "Untitled"),
                    content=kwargs.get("content", ""),
                    tags=kwargs.get("tags"),
                )
                return {"status": "created", "id": note_id}
            elif action == "list":
                notes = await memory.get_notes()
                return {"notes": notes}
            elif action == "search":
                notes = await memory.get_notes(query=kwargs.get("query", ""))
                return {"notes": notes}
            else:
                return {"error": f"Unknown action: {action}"}
        finally:
            await memory.close()
