"""EXER002 — Python Primer for AI Engineers (reference solution).

Every LLM API speaks JSON. In Python, JSON objects become dicts and JSON
arrays become lists. This exercise practises reading and building them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ValidationError

SAMPLE = Path(__file__).resolve().parent.parent / "sample_response.json"


# --------------------------------------------------------------- reading JSON
def load_response(path: str | Path) -> dict:
    """Read a JSON file and return it as a Python dict."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_reply_text(response: dict) -> str:
    """Return the assistant's text: response -> choices[0] -> message -> content."""
    return response["choices"][0]["message"]["content"]


def get_total_tokens(response: dict) -> int:
    """Return usage.total_tokens."""
    return response["usage"]["total_tokens"]


def safe_get_reply(response: dict) -> str | None:
    """Like get_reply_text, but return None instead of crashing on a malformed response."""
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return None


# -------------------------------------------------------------- building JSON
def build_request(model: str, user_text: str, system_text: str | None = None) -> dict:
    """Build a chat request body.

    {"model": model, "messages": [ {system?}, {"role": "user", "content": user_text} ]}
    The system message is only included when system_text is given.
    """
    messages: list[dict] = []
    if system_text:
        messages.append({"role": "system", "content": system_text})
    messages.append({"role": "user", "content": user_text})
    return {"model": model, "messages": messages}


# ----------------------------------------------------- validating with Pydantic
class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


def parse_messages(raw: list[dict]) -> list[Message]:
    """Turn a list of dicts into validated Message objects (raises ValidationError if invalid)."""
    return [Message(**item) for item in raw]


def main() -> None:
    response = load_response(SAMPLE)
    print("Reply       :", get_reply_text(response))
    print("Tokens used :", get_total_tokens(response))
    print("Request body:", json.dumps(build_request("my-chat-model", "Hi!", "Be brief."), indent=2))
    try:
        parse_messages([{"role": "robot", "content": "beep"}])
    except ValidationError as exc:
        print("Validation caught a bad role:", exc.errors()[0]["msg"])


if __name__ == "__main__":
    main()
