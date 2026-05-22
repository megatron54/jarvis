"""Health check endpoints."""

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health_check(request: Request) -> dict:
    """Check system health."""
    ollama_ok = await request.app.state.ollama.health()
    memory_ok = await request.app.state.memory.health()

    return {
        "status": "healthy" if (ollama_ok and memory_ok) else "degraded",
        "services": {
            "ollama": "up" if ollama_ok else "down",
            "memory": "up" if memory_ok else "down",
        },
    }
