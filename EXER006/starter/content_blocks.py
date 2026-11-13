"""EXER006 — Message Content Blocks.

A message's `content` can be a plain string OR a list of typed blocks.
Blocks let one message carry text and images together.

    uv run python EXER006/starter/content_blocks.py
    uv run python EXER006/check.py
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
    """Return {"type": "text", "text": text}."""
    # TODO
    raise NotImplementedError("text_block")


def image_block_from_url(url: str, detail: str = "auto") -> dict:
    """Return {"type": "image_url", "image_url": {"url": url, "detail": detail}}."""
    # TODO
    raise NotImplementedError("image_block_from_url")


def image_block_from_file(path: str | Path, detail: str = "auto") -> dict:
    """Embed a local image as a base64 data URL.

    1. mime = mimetypes.guess_type(path.name)[0]   e.g. "image/png"
    2. encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    3. url = f"data:{mime};base64,{encoded}"
    4. return image_block_from_url(url, detail)
    """
    # TODO
    raise NotImplementedError("image_block_from_file")


def build_multimodal_message(text: str, image_paths: list[str | Path]) -> dict:
    """One USER message whose content is a list: the text block first,
    then one image block per path."""
    # TODO
    raise NotImplementedError("build_multimodal_message")


def describe_image(client, path: str | Path, question: str) -> str:
    """Send build_multimodal_message(question, [path]) to the model, return the reply text."""
    # TODO
    raise NotImplementedError("describe_image")


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

    Algorithm:
      - keep the first system message (if any); subtract its cost from the budget
      - walk the other messages from NEWEST to OLDEST, keeping each while it fits
      - stop at the first one that doesn't fit
      - return system + kept messages in their ORIGINAL order
    """
    # TODO
    raise NotImplementedError("trim_history")


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
