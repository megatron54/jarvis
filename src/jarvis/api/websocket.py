"""WebSocket endpoint for real-time streaming chat."""

from fastapi import WebSocket, WebSocketDisconnect
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info("WebSocket connected", session_id=session_id)

    def disconnect(self, session_id: str) -> None:
        self.active_connections.pop(session_id, None)
        logger.info("WebSocket disconnected", session_id=session_id)

    async def send_text(self, session_id: str, text: str) -> None:
        ws = self.active_connections.get(session_id)
        if ws:
            await ws.send_text(text)


manager = ConnectionManager()


def register_websocket(app) -> None:
    """Register WebSocket endpoint on the FastAPI app."""

    @app.websocket("/ws/{session_id}")
    async def websocket_chat(websocket: WebSocket, session_id: str):
        await manager.connect(websocket, session_id)
        try:
            while True:
                data = await websocket.receive_json()
                content = data.get("content", "")

                if not content:
                    continue

                ollama = websocket.app.state.ollama
                memory = websocket.app.state.memory

                history = await memory.get_conversation(session_id)
                history.append({"role": "user", "content": content})

                # Stream response
                full_response = ""
                async for chunk in ollama.chat_stream(messages=history[-20:]):
                    full_response += chunk
                    await websocket.send_json({"type": "chunk", "content": chunk})

                await websocket.send_json({"type": "done", "content": full_response})

                history.append({"role": "assistant", "content": full_response})
                await memory.save_conversation(session_id, history)

        except WebSocketDisconnect:
            manager.disconnect(session_id)
