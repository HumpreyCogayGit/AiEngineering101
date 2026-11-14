"""EXER002 stretch goal 1 — a `tool` message with its required id.

    uv run python EXER002/stretch/goal1_tool_role.py

A tool result (EXER016) is a message with role "tool". Unlike the other
roles it MUST say which tool call it answers, in `tool_call_id`. One model
per shape keeps that rule in the type instead of in an if-statement.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ValidationError

from aicourse.stretch import solution_module

base = solution_module(__file__, "primer.py")


class ToolMessage(BaseModel):
    role: Literal["tool"]
    content: str
    tool_call_id: str  # no default, so it is required


def parse_messages(raw: list[dict]) -> list[BaseModel]:
    """Like the exercise's parse_messages, but tool messages get their own model."""
    return [ToolMessage(**item) if item.get("role") == "tool" else base.Message(**item) for item in raw]


def main() -> None:
    good = parse_messages([
        {"role": "user", "content": "Weather in Tokyo?"},
        {"role": "tool", "content": '{"temp_c": 18}', "tool_call_id": "call_1"},
    ])
    print("Parsed:", [type(m).__name__ for m in good])
    try:
        parse_messages([{"role": "tool", "content": '{"temp_c": 18}'}])
    except ValidationError as exc:
        error = exc.errors()[0]
        print(f"Rejected a tool message without an id: {error['loc'][0]}: {error['msg']}")


if __name__ == "__main__":
    main()
