"""EXER010 — Building a CLI App.

Build a real command-line tool around the LLM with Typer:

    uv run python EXER010/starter/ask.py --help
    uv run python EXER010/starter/ask.py ask "What is RAG?"
    uv run python EXER010/starter/ask.py ask "Explain DNS" --system "You are a teacher" -t 0.2
    uv run python EXER010/starter/ask.py chat
    uv run python EXER010/starter/ask.py summarize README.md --words 50
    cat README.md | uv run python EXER010/starter/ask.py summarize -

    uv run python EXER010/check.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from aicourse.llm import get_llm_client, model_params
from aicourse.settings import ConfigError, get_settings

app = typer.Typer(help="Ask an LLM from your terminal.", no_args_is_help=True)

EXIT_FILE_ERROR = 1
EXIT_CONFIG_ERROR = 2


def get_client():
    """Separate function so tests can replace it with a fake. (Given.)"""
    try:
        return get_llm_client()
    except ConfigError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_CONFIG_ERROR)


def stream_answer(messages: list[dict], temperature: float = 0.7) -> str:
    """Stream the reply to stdout and return the full text.

    Reuse what you learned in EXER007. Use get_client() (not get_llm_client())
    and typer.echo(piece, nl=False) to print each piece without a newline.
    Print one final newline at the end.
    Pass the temperature as **model_params(temperature=temperature) so the tool
    also works on models that reject a custom temperature.
    """
    # TODO
    raise NotImplementedError("stream_answer")


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="The question to ask")],
    system: Annotated[str, typer.Option("--system", "-s", help="System prompt")] = "You are a helpful assistant.",
    temperature: Annotated[float, typer.Option("--temperature", "-t", min=0.0, max=2.0)] = 0.7,
) -> None:
    """Ask a single question."""
    # TODO: call stream_answer with a system message and a user message
    raise NotImplementedError("ask command")


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
    """Read from a file path, or from stdin when file is '-'.

    If the file does not exist: print "Error: file not found: <file>" to STDERR
    (typer.echo(..., err=True)) and raise typer.Exit(EXIT_FILE_ERROR).
    """
    # TODO
    raise NotImplementedError("read_input")


# TODO: register this function as a command with @app.command()
def summarize(
    file: Annotated[str, typer.Argument(help="File to summarize, or - to read stdin")],
    words: Annotated[int, typer.Option("--words", "-w", min=10)] = 100,
) -> None:
    """Summarize a text file (or stdin)."""
    # TODO:
    #   1. text = read_input(file)
    #   2. if the text is empty/whitespace: print an error to stderr, exit with EXIT_FILE_ERROR
    #   3. stream_answer with system "Summarize the text in at most {words} words." and the text
    #      as the user message, temperature=0.3
    raise NotImplementedError("summarize command")


if __name__ == "__main__":
    app()
