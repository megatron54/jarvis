"""Jarvis CLI interface using Typer and Rich."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

app = typer.Typer(name="jarvis", help="Jarvis - Local AI Personal Assistant")
console = Console()


@app.command()
def chat(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override model"),
    session: str = typer.Option("default", "--session", "-s", help="Session ID"),
) -> None:
    """Start an interactive chat session."""
    asyncio.run(_chat_loop(model, session))


async def _chat_loop(model: str | None, session: str) -> None:
    """Main chat loop."""
    from jarvis.config import get_settings
    from jarvis.llm import OllamaClient
    from jarvis.memory.manager import MemoryManager
    from jarvis.tools.registry import ToolRegistry

    settings = get_settings()
    ollama = OllamaClient(base_url=settings.ollama_base_url)
    memory = MemoryManager(
        redis_url=settings.redis_url,
        database_url=settings.database_url,
        chroma_url=settings.chroma_url,
    )
    tools = ToolRegistry()

    await memory.initialize()
    tools.discover()

    console.print(Panel(
        "[bold cyan]JARVIS[/bold cyan] - Local AI Assistant\n"
        f"Model: {model or settings.default_model}\n"
        "Type 'exit' to quit, 'clear' to reset conversation",
        title="Welcome",
        border_style="cyan",
    ))

    system_prompt = (
        "You are Jarvis, a local AI personal assistant. "
        "You are helpful, concise, and respect the user's privacy. "
        "Respond in the same language the user writes in."
    )

    history: list[dict] = await memory.get_conversation(session)

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input.strip():
            continue
        if user_input.strip().lower() == "exit":
            break
        if user_input.strip().lower() == "clear":
            history.clear()
            await memory.clear_conversation(session)
            console.print("[dim]Conversation cleared.[/dim]")
            continue

        history.append({"role": "user", "content": user_input})

        console.print("\n[bold cyan]Jarvis[/bold cyan]: ", end="")

        try:
            full_response = ""
            async for chunk in ollama.chat_stream(
                messages=[{"role": "system", "content": system_prompt}] + history[-20:],
                model=model or settings.default_model,
            ):
                console.print(chunk, end="")
                full_response += chunk

            console.print()  # newline
            history.append({"role": "assistant", "content": full_response})
            await memory.save_conversation(session, history)

        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")

    await memory.close()
    await ollama.close()
    console.print("\n[dim]Goodbye![/dim]")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8080, "--port"),
) -> None:
    """Start the Jarvis API server."""
    import uvicorn
    uvicorn.run("jarvis.main:app", host=host, port=port, reload=False)


@app.command()
def status() -> None:
    """Check Jarvis system status."""
    asyncio.run(_check_status())


async def _check_status() -> None:
    from jarvis.config import get_settings
    from jarvis.llm import OllamaClient

    settings = get_settings()
    ollama = OllamaClient(base_url=settings.ollama_base_url)

    console.print(Panel("System Status", border_style="cyan"))

    # Check Ollama
    if await ollama.health():
        models = await ollama.list_models()
        console.print(f"  [green]✓[/green] Ollama: {len(models)} models available")
        for m in models[:5]:
            console.print(f"    - {m['name']}")
    else:
        console.print("  [red]✗[/red] Ollama: unreachable")

    await ollama.close()


if __name__ == "__main__":
    app()
