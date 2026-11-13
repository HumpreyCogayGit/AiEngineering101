"""EXER002 — Python Primer for AI Engineers.

Every LLM API speaks JSON. In Python, JSON objects become dicts and JSON
arrays become lists. Complete every TODO, then run:

    uv run python EXER002/starter/primer.py
    uv run python EXER002/check.py

Open EXER002/sample_response.json first and look at its shape.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

SAMPLE = Path(__file__).resolve().parent.parent / "sample_response.json"


# --------------------------------------------------------------- reading JSON
def load_response(path: str | Path) -> dict:
    """Read a JSON file and return it as a Python dict.

    Hint: open the file with `with open(path, encoding="utf-8") as f:` and use json.load(f).
    """
    # TODO
    raise NotImplementedError("load_response")


def get_reply_text(response: dict) -> str:
    """Return the assistant's text: response -> choices[0] -> message -> content.

    Hint: chain the lookups: response["choices"][0][...][...]
    """
    # TODO
    raise NotImplementedError("get_reply_text")


def get_total_tokens(response: dict) -> int:
    """Return usage.total_tokens."""
    # TODO
    raise NotImplementedError("get_total_tokens")


def safe_get_reply(response: dict) -> str | None:
    """Like get_reply_text, but return None instead of crashing on a malformed response.

    Hint: wrap the lookup in try/except and catch KeyError, IndexError and TypeError.
    """
    # TODO
    raise NotImplementedError("safe_get_reply")


# -------------------------------------------------------------- building JSON
def build_request(deployment: str, user_text: str, system_text: str | None = None) -> dict:
    """Build a chat request body.

    {"model": deployment, "messages": [ {system?}, {"role": "user", "content": user_text} ]}
    The system message is only included when system_text is given, and it comes FIRST.
    """
    # TODO
    raise NotImplementedError("build_request")


# ----------------------------------------------------- validating with Pydantic
class Message(BaseModel):
    """A chat message. Pydantic checks the types for us when we create one."""

    # TODO: add two fields:
    #   role    — only "system", "user" or "assistant" allowed (hint: Literal[...])
    #   content — a str
    pass


def parse_messages(raw: list[dict]) -> list[Message]:
    """Turn a list of dicts into validated Message objects (raises ValidationError if invalid).

    Hint: Message(**item) unpacks a dict into keyword arguments.
    """
    # TODO
    raise NotImplementedError("parse_messages")


def main() -> None:
    response = load_response(SAMPLE)
    print("Reply       :", get_reply_text(response))
    print("Tokens used :", get_total_tokens(response))
    print("Request body:", json.dumps(build_request("gpt-4.1-mini", "Hi!", "Be brief."), indent=2))
    try:
        parse_messages([{"role": "robot", "content": "beep"}])
    except ValidationError as exc:
        print("Validation caught a bad role:", exc.errors()[0]["msg"])


if __name__ == "__main__":
    main()
