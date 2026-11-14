"""EXER007 stretch goal 1 — stop a stream with Ctrl-C and keep the partial reply.

    uv run python EXER007/stretch/goal1_interruptible_stream.py           # press Ctrl-C mid-answer
    uv run python EXER007/stretch/goal1_interruptible_stream.py --demo    # interrupts itself

Three things make an interruption clean:
1. catch KeyboardInterrupt around the loop that consumes the stream,
2. close the generator, which closes the HTTP response (the model stops being billed for output),
3. store what arrived as the assistant message, so the history stays truthful.
"""

from __future__ import annotations

import sys

from aicourse.llm import get_llm_client
from aicourse.stretch import solution_module

base = solution_module(__file__, "streaming.py")

INTERRUPTED_NOTE = " [interrupted by the user]"


def stream_interruptible(pieces, on_token=None) -> tuple[str, bool]:
    """Consume a stream. Returns (text so far, was it interrupted?)."""
    parts: list[str] = []
    try:
        for piece in pieces:
            parts.append(piece)
            if on_token:
                on_token(piece)
    except KeyboardInterrupt:
        pieces.close()  # runs the generator's cleanup: the connection is released
        return "".join(parts), True
    return "".join(parts), False


def chat_turn(client, messages: list[dict], text: str, on_token=None) -> bool:
    """One streamed turn. The partial reply is stored even when interrupted."""
    messages.append({"role": "user", "content": text})
    reply, interrupted = stream_interruptible(base.stream_reply(client, messages), on_token)
    messages.append({"role": "assistant", "content": reply + (INTERRUPTED_NOTE if interrupted else "")})
    return interrupted


def demo() -> None:
    client = get_llm_client()
    messages = [{"role": "system", "content": "You are a storyteller."}]
    seen = {"n": 0}

    def show(piece: str) -> None:
        print(piece, end="", flush=True)
        seen["n"] += 1
        if seen["n"] == 15:
            raise KeyboardInterrupt  # what Ctrl-C raises, after 15 pieces

    print("Bot: ", end="")
    interrupted = chat_turn(client, messages, "Tell me a 200-word story about a lighthouse.", show)
    print(f"\n\ninterrupted={interrupted}; stored reply has {len(messages[-1]['content'])} characters")
    print("Bot: ", end="")
    chat_turn(client, messages, "In one sentence: what had you told me before I stopped you?",
              lambda piece: print(piece, end="", flush=True))
    print()


def main() -> None:
    if "--demo" in sys.argv:
        return demo()
    client = get_llm_client()
    messages = [{"role": "system", "content": "You are a storyteller."}]
    print("Streaming chatbot. Ctrl-C stops an answer; /exit quits.")
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/exit":
            break
        if not text:
            continue
        print("Bot: ", end="", flush=True)
        if chat_turn(client, messages, text, lambda piece: print(piece, end="", flush=True)):
            print("\n(stopped; the partial answer is kept in the history)")
        else:
            print()


if __name__ == "__main__":
    main()
