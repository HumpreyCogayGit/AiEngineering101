"""EXER010 stretch goal 1 — a `--json` flag for scripts.

    uv run python EXER010/stretch/goal1_json_flag.py ask "What is RAG?"
    uv run python EXER010/stretch/goal1_json_flag.py ask "What is RAG?" --json
    uv run python EXER010/stretch/goal1_json_flag.py ask "What is RAG?" --json | python -m json.tool

Text is for people, JSON is for programs. With `--json` the command prints
exactly one JSON object on stdout and nothing else, so a script can parse it.
That is also why it does not stream: half a JSON object is useless.

The `chat` and `summarize` commands are reused from the reference solution.
"""

from __future__ import annotations

import json
from typing import Annotated

import typer

from aicourse.llm import model_params
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "ask.py")

app = typer.Typer(help="Ask an LLM from your terminal.", no_args_is_help=True)
app.command()(base.chat)
app.command()(base.summarize)


def answer_as_dict(messages: list[dict], temperature: float) -> dict:
    """One complete (non-streamed) call, as plain data."""
    response = base.get_client().chat.completions.create(
        model=get_settings().chat_model, messages=messages, **model_params(temperature=temperature)
    )
    choice = response.choices[0]
    return {
        "answer": choice.message.content or "",
        "finish_reason": choice.finish_reason,
        "model": get_settings().chat_model,
        "usage": {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        },
    }


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="The question to ask")],
    system: Annotated[str, typer.Option("--system", "-s", help="System prompt")] = "You are a helpful assistant.",
    temperature: Annotated[float, typer.Option("--temperature", "-t", min=0.0, max=2.0)] = 0.7,
    as_json: Annotated[bool, typer.Option("--json", help="Print one JSON object instead of streaming text")] = False,
) -> None:
    """Ask a single question."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": question}]
    if as_json:
        typer.echo(json.dumps(answer_as_dict(messages, temperature), ensure_ascii=False))
    else:
        base.stream_answer(messages, temperature)


if __name__ == "__main__":
    app()
