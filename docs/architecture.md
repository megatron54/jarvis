# Jarvis Architecture

## System Overview

Jarvis is a modular, local-first AI personal assistant built with privacy and extensibility as core principles.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        INTERFACES                            │
│   CLI │ Web UI │ WebSocket │ Voice │ Telegram │ REST API    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    API GATEWAY (FastAPI)                      │
│   CORS │ Auth │ Rate Limit │ Routing │ Streaming            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                AGENT ORCHESTRATOR (LangGraph)                 │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Router  │→ │ Planner  │→ │ Executor │→ │ Reviewer │   │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────┬───────────────┬───────────────┬──────────────────────┘
       │               │               │
┌──────▼───┐    ┌──────▼───┐    ┌──────▼───────────────────┐
│ MEMORY   │    │  TOOLS   │    │      LLM LAYER           │
│          │    │          │    │                           │
│ Redis    │    │ Notes    │    │  Ollama                   │
│ (short)  │    │ Tasks    │    │  ├─ qwen2.5:14b (main)   │
│          │    │ Files    │    │  ├─ qwen2.5:3b (fast)    │
│ Postgres │    │ System   │    │  ├─ coder:7b (code)      │
│ (long)   │    │ Browser  │    │  └─ deepseek:14b (think) │
│          │    │ Calendar │    └──────────────────────────┘
│ ChromaDB │    │ Email    │
│ (vector) │    └──────────┘
└──────────┘         │
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  EVENT BUS (Redis Pub/Sub)                    │
└──────────────────────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│               CONNECTORS / INTEGRATIONS                      │
│  Telegram │ GitHub │ Google │ Notion │ Home Assistant        │
└──────────────────────────────────────────────────────────────┘
```

## Memory Architecture

### Three-tier memory system:

1. **Short-term (Redis)**: Active conversation, session state, working context
2. **Long-term (PostgreSQL)**: User preferences, task history, interaction logs
3. **Semantic (ChromaDB)**: Embedded knowledge, notes, conversation summaries for RAG

### Context Window Management:
- Last 20 messages kept in full
- Older messages compressed into summaries
- RAG retrieval for relevant past context
- User preferences always injected

## Security Model

### Permission Levels:
- **Level 0 (Safe)**: Read operations, queries → auto-execute
- **Level 1 (Moderate)**: Write ops, app launches → execute with logging
- **Level 2 (Dangerous)**: System commands, deletions → requires confirmation
- **Level 3 (Blocked)**: Destructive operations → never allowed

### Path Restrictions:
- System directories blocked (/etc, /boot, /sys, C:\Windows\System32)
- User can configure allowed/blocked paths
- All file operations logged

## Voice Pipeline

```
Mic → [Wake Word] → [VAD] → [STT] → [LLM] → [TTS] → Speaker
       OpenWakeWord   Silero   faster-   Ollama   Kokoro
       (~50ms)        (~10ms)  whisper   (~800ms) (~200ms)
                               (~500ms)
```

Total latency: ~1.5-2s end-to-end

## Hardware Profile (Target)

- **CPU**: i5-13600KF (14 cores)
- **GPU**: RTX 4060 Ti 16GB VRAM
- **RAM**: 32GB DDR4/DDR5
- **Storage**: NVMe SSD

### VRAM Budget:
- Main model (qwen2.5:14b-q4): ~10GB
- Whisper (small): ~1GB
- Remaining: ~5GB headroom
