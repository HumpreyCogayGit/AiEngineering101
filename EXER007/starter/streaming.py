"""EXER007 — Streaming.

With stream=True the API sends the answer in small chunks (server-sent
events) as it is generated. Complete every TODO, then run:

    uv run python EXER007/starter/streaming.py
    uv run python EXER007/check.py
"""

from __future__ import annotations

import time
from typing import Callable, Iterator

from aicourse.llm import get_openai_client
from aicourse.settings import get_settings


def stream_reply(client, messages: list[dict]) -> Iterator[str]:
    """Yield text pieces (deltas) as they arrive.

    1. stream = client.chat.completions.create(model=..., messages=messages, stream=True)
    2. for chunk in stream:
         - skip chunks where chunk.choices is empty
         - delta = chunk.choices[0].delta.content
         - if delta is not empty: yield delta
    This is a GENERATOR function (it uses `yield`, not `return`).
    """
    # TODO
    raise NotImplementedError("stream_reply")


def collect(pieces: Iterator[str], on_token: Callable[[str], None] | None = None) -> str:
    """Consume a stream, calling on_token(piece) for each piece (if given),
    and return the full joined text."""
    # TODO
    raise NotImplementedError("collect")


def stream_with_usage(client, messages: list[dict]) -> tuple[str, dict]:
    """Stream, and also return token usage.

    Pass stream_options={"include_usage": True}. The API then sends one extra
    LAST chunk whose `choices` is empty and whose `usage` is filled in.
    Return (full_text, {"prompt_tokens": .., "completion_tokens": .., "total_tokens": ..}).
    """
    # TODO
    raise NotImplementedError("stream_with_usage")


def measure(client, messages: list[dict]) -> dict:
    """Time-to-first-token vs total time — the reason streaming feels fast."""
    start = time.perf_counter()
    first: float | None = None
    count = 0
    for _ in stream_reply(client, messages):
        if first is None:
            first = time.perf_counter() - start
        count += 1
    total = time.perf_counter() - start
    return {"time_to_first_token": first or total, "total_time": total, "chunks": count}


def main() -> None:
    client = get_openai_client()
    messages = [{"role": "system", "content": "You are a storyteller."}]
    print("Streaming chatbot. Type /exit to quit.")
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/exit":
            break
        if not text:
            continue
        messages.append({"role": "user", "content": text})
        print("Bot: ", end="", flush=True)
        reply = collect(stream_reply(client, messages), lambda t: print(t, end="", flush=True))
        print()
        messages.append({"role": "assistant", "content": reply})

    stats = measure(client, [{"role": "user", "content": "Write a 150-word poem about rivers."}])
    print(f"\nFirst token after {stats['time_to_first_token']:.2f}s, "
          f"full answer after {stats['total_time']:.2f}s ({stats['chunks']} chunks)")


if __name__ == "__main__":
    main()
