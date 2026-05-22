# Jarvis - Local AI Personal Assistant

A fully local, privacy-first AI personal assistant powered by Ollama and open-source models.

## Features

- **100% Local** - All processing on your machine. No data leaves your system.
- **Multi-model** - Uses specialized models for different tasks (chat, coding, reasoning)
- **Tool System** - Extensible tools for notes, tasks, files, system control
- **Memory** - Persistent conversational and semantic memory
- **Voice** (planned) - Wake word + STT + TTS pipeline
- **Automation** (planned) - Browser control, system automation, workflows
- **Multi-interface** - CLI, REST API, Web UI

## Hardware Requirements

| Component | Minimum | Recommended (this project) |
|-----------|---------|---------------------------|
| GPU | 8GB VRAM | **RTX 4060 Ti 16GB** |
| RAM | 16GB | **32GB** |
| CPU | 6 cores | **i5-13600KF** |
| Storage | 50GB free | 100GB+ NVMe |

## Quick Start

### 1. Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- [Ollama](https://ollama.ai/) installed
- Python 3.11+

### 2. Clone & Setup

```bash
git clone https://github.com/megatron54/jarvis.git
cd jarvis
cp .env.example .env
```

### 3. Download Models

```bash
# Main chat model
ollama pull qwen2.5:14b-instruct-q4_K_M

# Fast model (routing, quick tasks)
ollama pull qwen2.5:3b

# Coding model
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Embeddings
ollama pull nomic-embed-text
```

### 4. Start Infrastructure

```bash
docker compose up -d postgres redis chromadb
```

### 5. Install & Run

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -e ".[dev]"

# Interactive chat
jarvis chat

# API server
jarvis serve
```

## Architecture

```
┌──────────────────────────────────────────────┐
│                 INTERFACES                     │
│        CLI │ REST API │ Web UI │ Voice        │
└─────────────────────┬────────────────────────┘
                      │
┌─────────────────────▼────────────────────────┐
│              FastAPI Gateway                   │
└─────────────────────┬────────────────────────┘
                      │
┌─────────────────────▼────────────────────────┐
│            Orchestrator (LangGraph)            │
│     Router → Planner → Executor → Reviewer   │
└──────┬──────────────┬───────────────┬────────┘
       │              │               │
┌──────▼──┐    ┌──────▼──┐    ┌──────▼──────┐
│ Memory  │    │  Tools  │    │  Ollama     │
│ Redis   │    │ Notes   │    │  qwen2.5    │
│ Postgres│    │ Tasks   │    │  coder      │
│ ChromaDB│    │ Files   │    │  deepseek   │
└─────────┘    │ System  │    └─────────────┘
               └─────────┘
```

## Project Structure

```
jarvis/
├── src/jarvis/          # Main source code
│   ├── api/             # FastAPI routes
│   ├── agents/          # LangGraph agents
│   ├── llm/             # Ollama client
│   ├── memory/          # Memory management
│   ├── tools/           # Tool implementations
│   ├── connectors/      # External integrations
│   ├── automation/      # System automation
│   ├── voice/           # STT/TTS pipeline
│   ├── events/          # Event bus
│   └── cli/             # CLI interface
├── frontend/            # Web UI (SvelteKit)
├── configs/             # Prompts, workflows
├── docker/              # Dockerfiles
├── tests/               # Test suite
└── scripts/             # Setup & utility scripts
```

## Models Used

| Use Case | Model | VRAM | Speed |
|----------|-------|------|-------|
| Chat | qwen2.5:14b-instruct-q4_K_M | ~10GB | ~30 t/s |
| Quick/Routing | qwen2.5:3b | ~2.5GB | ~80 t/s |
| Coding | qwen2.5-coder:7b-instruct-q4_K_M | ~5GB | ~50 t/s |
| Reasoning | deepseek-r1:14b | ~10GB | ~25 t/s |
| Embeddings | nomic-embed-text | ~300MB | Fast |

## Development Roadmap

- [x] **Phase 1** - MVP: Chat + CLI + API + Basic Tools
- [ ] **Phase 2** - Memory: ChromaDB RAG + Semantic Search
- [ ] **Phase 3** - Voice: Whisper STT + Kokoro TTS
- [ ] **Phase 4** - Automation: Browser + System Control
- [ ] **Phase 5** - Multi-Agent: LangGraph orchestration
- [ ] **Phase 6** - Ecosystem: All integrations + Web UI

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | System health check |
| POST | `/api/v1/chat` | Send message, get response |
| POST | `/api/v1/chat/stream` | Streaming response |
| GET | `/api/v1/tools` | List available tools |
| POST | `/api/v1/tools/{name}/execute` | Execute a tool |

## Configuration

Copy `.env.example` to `.env` and configure:

- `DEFAULT_MODEL` - Main chat model
- `OLLAMA_BASE_URL` - Ollama server URL
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection

## Tech Stack

- **LLM**: Ollama + Qwen2.5 family
- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Memory**: Redis (short-term), PostgreSQL (long-term), ChromaDB (semantic)
- **Orchestration**: LangGraph
- **Infrastructure**: Docker Compose
- **CLI**: Typer + Rich

## License

MIT
