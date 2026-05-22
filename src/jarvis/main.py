"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from jarvis.config import get_settings
from jarvis.api.routes import chat, health, tools
from jarvis.memory.manager import MemoryManager
from jarvis.llm.ollama_client import OllamaClient
from jarvis.tools.registry import ToolRegistry
from jarvis.events.bus import EventBus

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()
    logger.info("Starting Jarvis", version="0.1.0")

    # Initialize core services
    app.state.ollama = OllamaClient(base_url=settings.ollama_base_url)
    app.state.memory = MemoryManager(
        redis_url=settings.redis_url,
        database_url=settings.database_url,
        chroma_url=settings.chroma_url,
    )
    app.state.tools = ToolRegistry()
    app.state.events = EventBus(redis_url=settings.redis_url)

    await app.state.memory.initialize()
    await app.state.events.initialize()
    app.state.tools.discover()

    logger.info("Jarvis initialized successfully")
    yield

    # Cleanup
    await app.state.memory.close()
    await app.state.events.close()
    logger.info("Jarvis shut down")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Jarvis",
        description="Local AI Personal Assistant",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router, tags=["health"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(tools.router, prefix="/api/v1", tags=["tools"])

    return app


app = create_app()
