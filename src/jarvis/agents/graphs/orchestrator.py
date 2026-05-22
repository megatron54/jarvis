"""LangGraph multi-agent orchestration graph."""

from __future__ import annotations

from typing import Any, Literal

import structlog

logger = structlog.get_logger()


class OrchestratorGraph:
    """
    Multi-agent orchestration using a state-machine approach.
    
    Flow:
    1. Router classifies intent
    2. Based on intent, route to appropriate handler
    3. Handler may use tools, planner, or direct LLM
    4. Response reviewed and returned
    """

    def __init__(self, ollama_client: Any, memory: Any, tools: Any, settings: Any):
        self._ollama = ollama_client
        self._memory = memory
        self._tools = tools
        self._settings = settings

        from jarvis.agents.router import RouterAgent, PlannerAgent
        self._router = RouterAgent(ollama_client, settings)
        self._planner = PlannerAgent(ollama_client, settings)

    async def process(self, message: str, session_id: str = "default") -> dict:
        """Process a user message through the full agent pipeline."""

        # 1. Classify intent
        intent = await self._router.classify_intent(message)
        logger.info("Intent classified", intent=intent, message=message[:50])

        # 2. Get model for this intent
        model = self._router.get_model_for_intent(intent)

        # 3. Load context
        history = await self._memory.get_conversation(session_id)
        history.append({"role": "user", "content": message})

        # 4. Build system prompt with RAG context
        system_prompt = await self._build_context(message, session_id)

        # 5. Determine if we need tools
        needs_tools = intent in ("task", "system", "search")

        # 6. Generate response
        if needs_tools:
            response = await self._execute_with_tools(system_prompt, history, model)
        elif intent == "reason":
            response = await self._reason(system_prompt, history, model)
        else:
            response = await self._ollama.chat(
                messages=[{"role": "system", "content": system_prompt}] + history[-20:],
                model=model,
            )

        # 7. Save to memory
        history.append({"role": "assistant", "content": response["content"]})
        await self._memory.save_conversation(session_id, history)

        # 8. Index in semantic memory if substantive
        if len(response["content"]) > 100:
            try:
                if hasattr(self._memory, "_semantic") and self._memory._semantic:
                    await self._memory._semantic.add_conversation_summary(
                        session_id, f"User: {message}\nAssistant: {response['content'][:500]}"
                    )
            except Exception:
                pass

        return {
            "content": response["content"],
            "intent": intent,
            "model_used": model or self._settings.default_model,
            "tool_calls": response.get("tool_calls"),
        }

    async def _build_context(self, message: str, session_id: str) -> str:
        """Build rich context with RAG and preferences."""
        base = (
            "You are Jarvis, a local AI personal assistant. "
            "You are helpful, concise, and respect privacy. "
            "Respond in the user's language. Use tools when appropriate."
        )

        # Add user preferences
        prefs = await self._memory.get_user_preferences()
        if prefs:
            base += f"\n\nUser preferences: {prefs}"

        # RAG: search semantic memory for relevant context
        try:
            if hasattr(self._memory, "_semantic") and self._memory._semantic:
                relevant = await self._memory._semantic.search(message, n_results=3)
                if relevant:
                    context_str = "\n".join(r["content"][:200] for r in relevant)
                    base += f"\n\nRelevant context from memory:\n{context_str}"
        except Exception:
            pass

        return base

    async def _execute_with_tools(self, system_prompt: str, history: list, model: str | None) -> dict:
        """Execute a request that may need tool calls."""
        response = await self._ollama.chat(
            messages=[{"role": "system", "content": system_prompt}] + history[-20:],
            model=model,
            tools=self._tools.get_schemas(),
        )

        # Handle tool calls
        if response.get("tool_calls"):
            tool_results = await self._tools.execute_batch(response["tool_calls"])
            # Feed results back
            history.append({"role": "assistant", "content": response["content"], "tool_calls": response["tool_calls"]})
            for result in tool_results:
                history.append({"role": "tool", "content": str(result)})

            # Get final response incorporating tool results
            final = await self._ollama.chat(
                messages=[{"role": "system", "content": system_prompt}] + history[-20:],
                model=model,
            )
            return final

        return response

    async def _reason(self, system_prompt: str, history: list, model: str | None) -> dict:
        """Use reasoning model for complex analysis."""
        # DeepSeek-R1 produces think tags, we want to extract the final answer
        response = await self._ollama.chat(
            messages=[{"role": "system", "content": system_prompt}] + history[-20:],
            model=model or "deepseek-r1:14b",
        )

        content = response["content"]
        # Remove think tags if present
        if "<think>" in content and "</think>" in content:
            think_end = content.index("</think>") + len("</think>")
            content = content[think_end:].strip()
            response["content"] = content

        return response
