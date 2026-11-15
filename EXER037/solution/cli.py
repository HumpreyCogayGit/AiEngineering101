"""Nimbus Helpdesk — command line.

    uv run python EXER037/solution/cli.py --help
    uv run python EXER037/solution/cli.py ask "What is your refund policy?"
    uv run python EXER037/solution/cli.py chat
    uv run python EXER037/solution/cli.py eval
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Annotated

import typer

from assistant import Assistant, Reply

app = typer.Typer(help="Nimbus Helpdesk assistant.", no_args_is_help=True)


def get_assistant() -> Assistant:
    """Separate function so tests can swap in a fake."""
    return Assistant()


def show(reply: Reply, verbose: bool = False) -> None:
    typer.echo(reply.answer)
    if reply.blocked:
        typer.echo(f"[blocked: {', '.join(reply.reasons)}]", err=True)
    if verbose:
        typer.echo(f"[tools: {', '.join(reply.tools_used) or 'none'} | tokens: {reply.tokens}]")


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="Your question")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show tools used and tokens")] = False,
) -> None:
    """Ask one question."""
    reply = asyncio.run(get_assistant().ask(question, thread_id=uuid.uuid4().hex))
    show(reply, verbose)
    if reply.blocked:
        raise typer.Exit(1)


@app.command()
def chat(verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False) -> None:
    """Interactive chat with memory. Type /exit to quit."""

    async def loop() -> None:
        assistant = await get_assistant().setup()
        thread = uuid.uuid4().hex
        while True:
            try:
                text = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if text in ("/exit", "/quit"):
                break
            if text:
                typer.echo("bot> ", nl=False)
                show(await assistant.ask(text, thread), verbose)

    asyncio.run(loop())


@app.command("eval")
def run_eval(heldout: bool = typer.Option(False, "--heldout", help="Run the held-out set (once, at the end).")) -> None:
    """Run the evaluation set and write a report with a score per category."""
    from evaluate import main as evaluate_main

    passed = asyncio.run(evaluate_main(heldout=heldout))
    raise typer.Exit(0 if passed else 1)


if __name__ == "__main__":
    app()
