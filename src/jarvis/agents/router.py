"""LangGraph-based agent router."""

from __future__ import annotations

from typing import Any, TypedDict

import structlog

logger = structlog.get_logger()


class AgentState(TypedDict):
    """State passed between agent nodes."""
    messages: list[dict]
    current_intent: str
    tool_results: list[Any]
    final_response: str
    model_override: str | None


class RouterAgent:
    """Routes user messages to the appropriate handler/model."""

    # Intent categories and their preferred models
    INTENT_MAP = {
        "chat": {"model": None, "description": "General conversation"},
        "code": {"model": "coding", "description": "Code generation or debugging"},
        "task": {"model": None, "description": "Task/note management"},
        "system": {"model": None, "description": "System commands or file ops"},
        "reason": {"model": "reasoning", "description": "Complex reasoning or analysis"},
        "search": {"model": None, "description": "Information retrieval from memory"},
    }

    CLASSIFICATION_PROMPT = """Classify the user's intent into exactly one category.
Categories: chat, code, task, system, reason, search

Rules:
- "chat" = casual conversation, questions, greetings
- "code" = writing, debugging, explaining code
- "task" = creating/managing tasks, notes, reminders, todos
- "system" = file operations, running commands, opening apps
- "reason" = complex analysis, planning, multi-step thinking
- "search" = finding information from notes, history, knowledge

Respond with ONLY the category name, nothing else.

User message: {message}
Category:"""

    def __init__(self, ollama_client: Any, settings: Any):
        self._ollama = ollama_client
        self._settings = settings

    async def classify_intent(self, message: str) -> str:
        """Classify user intent using the fast model."""
        prompt = self.CLASSIFICATION_PROMPT.format(message=message)

        response = await self._ollama.chat(
            messages=[{"role": "user", "content": prompt}],
            model=self._settings.fast_model,
        )

        intent = response["content"].strip().lower()
        # Validate
        if intent not in self.INTENT_MAP:
            intent = "chat"

        logger.debug("Intent classified", message=message[:50], intent=intent)
        return intent

    def get_model_for_intent(self, intent: str) -> str | None:
        """Get the recommended model for an intent."""
        info = self.INTENT_MAP.get(intent, {})
        model_key = info.get("model")

        if model_key == "coding":
            return self._settings.coding_model
        elif model_key == "reasoning":
            return "deepseek-r1:14b"

        return None  # Use default model


class PlannerAgent:
    """Breaks complex tasks into steps."""

    PLANNING_PROMPT = """You are a task planner. Break down the user's request into a list of concrete steps.
Each step should be a single action that can be executed by one tool.

Available tools: notes, tasks, files, system, get_datetime

Format your response as a numbered list of steps. Be concise.

User request: {request}
Steps:"""

    def __init__(self, ollama_client: Any, settings: Any):
        self._ollama = ollama_client
        self._settings = settings

    async def plan(self, request: str) -> list[str]:
        """Create a plan for a complex request."""
        prompt = self.PLANNING_PROMPT.format(request=request)

        response = await self._ollama.chat(
            messages=[{"role": "user", "content": prompt}],
            model=self._settings.default_model,
        )

        # Parse numbered list
        steps = []
        for line in response["content"].strip().split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering
                clean = line.lstrip("0123456789.-) ").strip()
                if clean:
                    steps.append(clean)

        return steps
