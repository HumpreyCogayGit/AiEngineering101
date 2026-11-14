"""EXER010 stretch goal 2 — a `classify` command that reuses the EXER008 prompt.

    uv run python EXER010/stretch/goal2_classify_command.py classify "I was charged twice"
    echo "The app crashes on start" | uv run python EXER010/stretch/goal2_classify_command.py classify -

A prompt you measured (EXER008) is an asset: wrap it in a command and it can
route tickets from a shell script. stdout carries the label and nothing else;
an answer outside the label set exits with code 3, so a script can tell.
"""

from __future__ import annotations

from typing import Annotated

import typer

from aicourse.stretch import solution_module

base = solution_module(__file__, "ask.py")
prompts = solution_module(__file__, "prompts.py", exercise="EXER008")

EXIT_UNKNOWN_LABEL = 3

app = typer.Typer(help="Ask an LLM from your terminal.", no_args_is_help=True)
for command in (base.ask, base.chat, base.summarize):
    app.command()(command)


@app.command()
def classify(
    ticket: Annotated[str, typer.Argument(help="The ticket text, or - to read stdin")],
) -> None:
    """Classify a support ticket: billing, technical, account or other."""
    text = base.read_input("-") if ticket == "-" else ticket
    if not text.strip():
        typer.echo("Error: input is empty", err=True)
        raise typer.Exit(base.EXIT_FILE_ERROR)
    label = prompts.classify(base.get_client(), prompts.build_messages_v3(text.strip()))
    if label == "unknown":
        typer.echo("Error: the model did not answer with a known label", err=True)
        raise typer.Exit(EXIT_UNKNOWN_LABEL)
    typer.echo(label)


if __name__ == "__main__":
    app()
