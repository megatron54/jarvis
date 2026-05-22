# Changelog

## [0.3.0] - 2026-05-23

### Added - Phase 5: Multi-Agent Orchestration
- `OrchestratorGraph`: Full multi-agent pipeline (Router → Planner → Executor → Reviewer)
- Intent-based model routing (chat, code, task, system, reason, search)
- DeepSeek-R1 integration for complex reasoning with think-tag parsing
- RAG context injection from semantic memory into prompts
- Google Calendar/Gmail connector (OAuth2)
- Notion connector (API key)
- Automatic conversation indexing in semantic memory

## [0.2.0] - 2026-05-23

### Added - Phase 2-4
- **Semantic Memory**: ChromaDB integration with embedding search via Ollama
- **Agent Router**: Intent classification using fast model (qwen2.5:3b)
- **Planner Agent**: Task decomposition for complex requests
- **WebSocket**: Real-time streaming chat endpoint
- **Voice STT**: faster-whisper engine with VAD filtering
- **Voice TTS**: Kokoro TTS with streaming synthesis
- **Voice Pipeline**: Wake word → STT → LLM → TTS flow
- **Browser Automation**: Playwright-based web control
- **System Control**: App launching, clipboard, notifications, scripts
- **Workflow Engine**: Multi-step automation with YAML definitions
- **Permission System**: 4-level security (safe/moderate/dangerous/blocked)
- **Telegram Connector**: Bot API integration
- **GitHub Connector**: Repos, issues, PRs

## [0.1.0] - 2026-05-23

### Added - Phase 1: MVP
- FastAPI backend with streaming chat endpoint
- Ollama client with chat, streaming, and embeddings support
- CLI interface with Rich/Typer (interactive mode)
- Tool system with registry and auto-discovery
- Tools: datetime, notes, tasks, files, system
- Memory manager: Redis (short-term), PostgreSQL (long-term)
- Event bus via Redis Pub/Sub
- Docker Compose: Ollama, PostgreSQL 16, Redis 7, ChromaDB
- Security: permission levels, path restrictions, command blocking
- Full project structure and configuration
