"""EXER006 checks. Run:  uv run python EXER006/check.py"""

import base64
from pathlib import Path

from aicourse.check import Checker
from aicourse.fakes import FakeClient
from aicourse.llm import get_openai_client

checker = Checker(__file__)
mod = checker.load("content_blocks.py")
IMAGE = Path(__file__).parent / "images" / "shapes.png"


@checker.check("text_block() and image_block_from_url() have the right shape")
def _():
    assert mod.text_block("hi") == {"type": "text", "text": "hi"}
    assert mod.image_block_from_url("https://x/y.png") == {
        "type": "image_url", "image_url": {"url": "https://x/y.png", "detail": "auto"}}


@checker.check("image_block_from_file() builds a valid base64 PNG data URL")
def _():
    url = mod.image_block_from_file(IMAGE)["image_url"]["url"]
    assert url.startswith("data:image/png;base64,"), url[:40]
    raw = base64.b64decode(url.split(",", 1)[1])
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "decoded data is not a PNG"


@checker.check("build_multimodal_message() = user message, text first, then images")
def _():
    msg = mod.build_multimodal_message("What is this?", [IMAGE, IMAGE])
    assert msg["role"] == "user"
    assert [b["type"] for b in msg["content"]] == ["text", "image_url", "image_url"]


@checker.check("describe_image() sends a content LIST to the model")
def _():
    fake = FakeClient(["a red circle"])
    assert mod.describe_image(fake, IMAGE, "what?") == "a red circle"
    assert isinstance(fake.calls[0]["messages"][0]["content"], list)


@checker.check("trim_history() keeps system + newest messages in order")
def _():
    msgs = [{"role": "system", "content": "S"}] + [
        {"role": "user" if i % 2 == 0 else "assistant", "content": str(i)} for i in range(10)
    ]
    out = mod.trim_history(msgs, max_tokens=4, count_fn=lambda m: 1)
    assert [m["content"] for m in out] == ["S", "7", "8", "9"], [m["content"] for m in out]


@checker.check("trim_history() returns everything when it already fits")
def _():
    msgs = [{"role": "system", "content": "S"}, {"role": "user", "content": "a"}]
    assert mod.trim_history(msgs, max_tokens=100, count_fn=lambda m: 1) == msgs


@checker.check("the model sees the shapes in the image  [live API]")
def _():
    answer = mod.describe_image(get_openai_client(), IMAGE, "Name the colours of the shapes. Be brief.").lower()
    hits = sum(c in answer for c in ("red", "blue", "green"))
    assert hits >= 2, answer


checker.run()
