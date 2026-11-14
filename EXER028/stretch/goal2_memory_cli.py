"""EXER028 stretch goal 2 — a small CLI to list and delete long-term memories.

    uv run python EXER028/stretch/goal2_memory_cli.py chat bea "I'm Bea, allergic to dairy, I love oat milk."
    uv run python EXER028/stretch/goal2_memory_cli.py list bea
    uv run python EXER028/stretch/goal2_memory_cli.py delete bea <id>
    uv run python EXER028/stretch/goal2_memory_cli.py forget bea

Memory is stored personal data, so a user must be able to see it and remove
it. The exercise keeps memories in an InMemoryStore, which is empty again in
every process. A CLI needs them to survive, so this one uses SqliteStore: the
same Store interface (search, put, delete), kept in a file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated

import typer
from langgraph.store.sqlite import SqliteStore

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "memory_bot.py")

DB = Path(__file__).resolve().parent / "output" / "memories.sqlite"
app = typer.Typer(help="Inspect and delete what the assistant remembers about a user.", no_args_is_help=True)


def open_store() -> SqliteStore:
    DB.parent.mkdir(parents=True, exist_ok=True)
    store = SqliteStore(sqlite3.connect(str(DB), check_same_thread=False, isolation_level=None))
    store.setup()  # creates the tables on first use
    return store


@app.command()
def chat(user: str, message: str) -> None:
    """Send one message as USER; durable facts in it are saved."""
    graph = base.build_chatbot(get_chat_model(temperature=0), store=open_store())
    typer.echo(base.send(graph, message, thread_id=f"cli-{user}", user_id=user))


@app.command("list")
def list_memories(user: str) -> None:
    """Show every memory stored for USER, with its id."""
    items = open_store().search(base.namespace(user))
    if not items:
        typer.echo(f"No memories stored for {user}.")
        return
    for item in items:
        typer.echo(f"{item.key}  {item.value['fact']}")


@app.command()
def delete(user: str, memory_id: Annotated[str, typer.Argument(help="An id shown by `list`")]) -> None:
    """Delete one memory of USER."""
    store = open_store()
    if store.get(base.namespace(user), memory_id) is None:
        typer.echo(f"Error: {user} has no memory with id {memory_id}", err=True)
        raise typer.Exit(1)
    store.delete(base.namespace(user), memory_id)
    typer.echo("Deleted.")


@app.command()
def forget(user: str) -> None:
    """Delete everything stored about USER."""
    store = open_store()
    items = store.search(base.namespace(user))
    for item in items:
        store.delete(base.namespace(user), item.key)
    typer.echo(f"Deleted {len(items)} memories of {user}.")


if __name__ == "__main__":
    app()
