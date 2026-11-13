"""EXER006 — Message Content Blocks (reference solution).

A message's `content` can be a plain string OR a list of typed blocks.
Blocks let one message carry text and images together.
"""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Callable

from aicourse.llm import get_openai_client
from aicourse.settings import get_settings

IMAGES = Path(__file__).resolve().parent.parent / "images"


# ------------------------------------------------------------------ blocks
def text_block(text: str) -> dict:
    return {"type": "text", "text": text}


def image_block_from_url(url: str, detail: str = "auto") -> dict:
    return {"type": "image_url", "image_url": {"url": url, "detail": detail}}


def image_block_from_file(path: str | Path, detail: str = "auto") -> dict:
    """Embed a local image as a base64 data URL."""
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return image_block_from_url(f"data:{mime};base64,{encoded}", detail)


def build_multimodal_message(text: str, image_paths: list[str | Path]) -> dict:
    """One user message: the text block first, then one image block per path."""
    content = [text_block(text)] + [image_block_from_file(p) for p in image_paths]
    return {"role": "user", "content": content}


def describe_image(client, path: str | Path, question: str) -> str:
    response = client.chat.completions.create(
        model=get_settings().chat_deployment,
        messages=[build_multimodal_message(question, [path])],
    )
    return response.choices[0].message.content or ""


# --------------------------------------------------------- context window
def approx_tokens(message: dict) -> int:
    """Rough token estimate: ~4 characters per token (good enough for budgeting)."""
    content = message["content"]
    if isinstance(content, str):
        return len(content) // 4 + 4
    total = 4
    for block in content:
        total += len(block.get("text", "")) // 4 if block["type"] == "text" else 85
    return total


def trim_history(
    messages: list[dict],
    max_tokens: int,
    count_fn: Callable[[dict], int] = approx_tokens,
) -> list[dict]:
    """Keep the system message plus the MOST RECENT messages that fit in max_tokens.

    The order of kept messages is preserved.
    """
    system = [m for m in messages if m["role"] == "system"][:1]
    rest = [m for m in messages if m["role"] != "system"]
    budget = max_tokens - sum(count_fn(m) for m in system)
    kept: list[dict] = []
    for message in reversed(rest):
        cost = count_fn(message)
        if cost > budget:
            break
        kept.append(message)
        budget -= cost
    return system + list(reversed(kept))


def main() -> None:
    client = get_openai_client()
    image = IMAGES / "shapes.png"
    print("Q: What shapes do you see, and what colour is each?")
    print("A:", describe_image(client, image, "What shapes do you see, and what colour is each?"))

    history = [{"role": "system", "content": "You are helpful."}]
    for i in range(20):
        history.append({"role": "user", "content": f"Question number {i}: " + "blah " * 30})
        history.append({"role": "assistant", "content": f"Answer number {i}: " + "ok " * 30})
    trimmed = trim_history(history, max_tokens=400)
    print(f"\nHistory: {len(history)} messages -> trimmed to {len(trimmed)} to fit 400 tokens")
    print("First kept non-system message:", trimmed[1]["content"][:30])


if __name__ == "__main__":
    main()
