"""EXER010 — Building a CLI App (reference solution).

A real command-line tool around the LLM:

    uv run python EXER010/solution/ask.py --help
    uv run python EXER010/solution/ask.py ask "What is RAG?"
    uv run python EXER010/solution/ask.py ask "Explain DNS" --system "You are a teacher" -t 0.2
    uv run python EXER010/solution/ask.py chat
    uv run python EXER010/solution/ask.py summarize README.md --words 50
    cat README.md | uv run python EXER010/solution/ask.py summarize -
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Iterator

import typer

from aicourse.llm import get_openai_client, model_params
from aicourse.settings import ConfigError, get_settings

app = typer.Typer(help="Ask an LLM from your terminal.", no_args_is_help=True)

EXIT_FILE_ERROR = 1
EXIT_CONFIG_ERROR = 2


def get_client():
    """Separate function so tests can replace it with a fake."""
    try:
        return get_openai_client()
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_CONFIG_ERROR)


def stream_answer(messages: list[dict], temperature: float = 0.7) -> str:
    """Stream the reply to stdout and return the full text."""
    stream = get_client().chat.completions.create(
        model=get_settings().chat_deployment,
        messages=messages,
        stream=True,
        **model_params(temperature=temperature),
    )
    parts: list[str] = []
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            piece = chunk.choices[0].delta.content
            parts.append(piece)
            typer.echo(piece, nl=False)
    typer.echo()
    return "".join(parts)


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="The question to ask")],
    system: Annotated[str, typer.Option("--system", "-s", help="System prompt")] = "You are a helpful assistant.",
    temperature: Annotated[float, typer.Option("--temperature", "-t", min=0.0, max=2.0)] = 0.7,
) -> None:
    """Ask a single question."""
    stream_answer(
        [{"role": "system", "content": system}, {"role": "user", "content": question}],
        temperature,
    )


@app.command()
def chat(
    system: Annotated[str, typer.Option("--system", "-s")] = "You are a helpful assistant.",
) -> None:
    """Start an interactive chat. Type /exit to quit."""
    messages = [{"role": "system", "content": system}]
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text in ("/exit", "/quit"):
            break
        if not text:
            continue
        messages.append({"role": "user", "content": text})
        typer.echo("bot> ", nl=False)
        messages.append({"role": "assistant", "content": stream_answer(messages)})


def read_input(file: str) -> str:
    """Read from a file path, or from stdin when file is '-'."""
    if file == "-":
        return sys.stdin.read()
    path = Path(file)
    if not path.is_file():
        typer.echo(f"Error: file not found: {file}", err=True)
        raise typer.Exit(EXIT_FILE_ERROR)
    return path.read_text(encoding="utf-8")


@app.command()
def summarize(
    file: Annotated[str, typer.Argument(help="File to summarize, or - to read stdin")],
    words: Annotated[int, typer.Option("--words", "-w", min=10)] = 100,
) -> None:
    """Summarize a text file (or stdin)."""
    text = read_input(file)
    if not text.strip():
        typer.echo("Error: input is empty", err=True)
        raise typer.Exit(EXIT_FILE_ERROR)
    stream_answer([
        {"role": "system", "content": f"Summarize the text in at most {words} words."},
        {"role": "user", "content": text},
    ], temperature=0.3)


if __name__ == "__main__":
    app()
