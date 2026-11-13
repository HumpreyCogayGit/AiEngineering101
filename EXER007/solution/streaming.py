"""EXER007 — Streaming (reference solution).

With stream=True the API sends the answer in small chunks (server-sent
events) as it is generated. The user sees text immediately instead of
waiting for the whole answer.
"""

from __future__ import annotations

import time
from typing import Callable, Iterator

from aicourse.llm import get_llm_client
from aicourse.settings import get_settings


def stream_reply(client, messages: list[dict]) -> Iterator[str]:
    """Yield text pieces (deltas) as they arrive."""
    stream = client.chat.completions.create(
        model=get_settings().chat_model,
        messages=messages,
        stream=True,
    )
    for chunk in stream:
        # Some chunks (e.g. the usage chunk, or Azure's first content-filter chunk)
        # have no choices, and some deltas have no content.
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def collect(pieces: Iterator[str], on_token: Callable[[str], None] | None = None) -> str:
    """Consume a stream, calling on_token for each piece, and return the full text."""
    parts: list[str] = []
    for piece in pieces:
        if on_token:
            on_token(piece)
        parts.append(piece)
    return "".join(parts)


def stream_with_usage(client, messages: list[dict]) -> tuple[str, dict]:
    """Stream, and also return token usage (sent in a final chunk with empty choices)."""
    stream = client.chat.completions.create(
        model=get_settings().chat_model,
        messages=messages,
        stream=True,
        stream_options={"include_usage": True},
    )
    parts: list[str] = []
    usage: dict = {}
    for chunk in stream:
        if chunk.usage:
            usage = {
                "prompt_tokens": chunk.usage.prompt_tokens,
                "completion_tokens": chunk.usage.completion_tokens,
                "total_tokens": chunk.usage.total_tokens,
            }
        if chunk.choices and chunk.choices[0].delta.content:
            parts.append(chunk.choices[0].delta.content)
    return "".join(parts), usage


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
    client = get_llm_client()
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
