"""Chat endpoints with streaming support."""

from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class ChatMessage(BaseModel):
    role: str = "user"
    content: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    role: str = "assistant"
    content: str
    session_id: str
    tool_calls: list[dict] | None = None


@router.post("/chat")
async def chat(request: Request, message: ChatMessage) -> ChatResponse:
    """Send a message and get a response."""
    ollama = request.app.state.ollama
    memory = request.app.state.memory
    tools = request.app.state.tools

    # Load conversation history
    history = await memory.get_conversation(message.session_id)
    history.append({"role": message.role, "content": message.content})

    # Get system prompt with context
    system_prompt = await _build_system_prompt(memory, message.session_id)

    # Generate response
    response = await ollama.chat(
        messages=[{"role": "system", "content": system_prompt}] + history,
        tools=tools.get_schemas(),
    )

    # Handle tool calls if present
    if response.get("tool_calls"):
        tool_results = await tools.execute_batch(response["tool_calls"])
        # Add tool results and get final response
        history.append({"role": "assistant", "content": response["content"], "tool_calls": response["tool_calls"]})
        for result in tool_results:
            history.append({"role": "tool", "content": str(result)})
        response = await ollama.chat(
            messages=[{"role": "system", "content": system_prompt}] + history,
        )

    # Save to memory
    assistant_msg = {"role": "assistant", "content": response["content"]}
    history.append(assistant_msg)
    await memory.save_conversation(message.session_id, history)

    return ChatResponse(
        role="assistant",
        content=response["content"],
        session_id=message.session_id,
        tool_calls=response.get("tool_calls"),
    )


@router.post("/chat/stream")
async def chat_stream(request: Request, message: ChatMessage) -> StreamingResponse:
    """Send a message and get a streaming response."""
    ollama = request.app.state.ollama
    memory = request.app.state.memory

    history = await memory.get_conversation(message.session_id)
    history.append({"role": message.role, "content": message.content})
    system_prompt = await _build_system_prompt(memory, message.session_id)

    async def generate() -> AsyncGenerator[str, None]:
        full_response = ""
        async for chunk in ollama.chat_stream(
            messages=[{"role": "system", "content": system_prompt}] + history,
        ):
            full_response += chunk
            yield chunk

        # Save after streaming completes
        history.append({"role": "assistant", "content": full_response})
        await memory.save_conversation(message.session_id, history)

    return StreamingResponse(generate(), media_type="text/plain")


async def _build_system_prompt(memory: "MemoryManager", session_id: str) -> str:
    """Build system prompt with user context."""
    base_prompt = (
        "You are Jarvis, a local AI personal assistant. "
        "You are helpful, concise, and respect the user's privacy. "
        "All processing happens locally on the user's machine. "
        "You can use tools to accomplish tasks. "
        "Respond in the same language the user writes in."
    )

    # Add user preferences if available
    preferences = await memory.get_user_preferences()
    if preferences:
        base_prompt += f"\n\nUser preferences: {preferences}"

    return base_prompt
