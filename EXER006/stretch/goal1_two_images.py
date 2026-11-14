"""EXER006 stretch goal 1 — two images in one message.

    uv run python EXER006/stretch/goal1_two_images.py

`content` is a list, so it can hold several image blocks. A short text block
before each image gives the model a name to refer to ("the first image").
"""

from __future__ import annotations

from aicourse.llm import get_llm_client
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "content_blocks.py")

FIRST = base.IMAGES / "shapes.png"
SECOND = base.IMAGES / "shapes_changed.png"


def comparison_message(question: str, first, second) -> dict:
    return {
        "role": "user",
        "content": [
            base.text_block(question),
            base.text_block("First image:"),
            base.image_block_from_file(first),
            base.text_block("Second image:"),
            base.image_block_from_file(second),
        ],
    }


def main() -> None:
    question = "List every difference between the two images, one per line."
    message = comparison_message(question, FIRST, SECOND)
    print("Blocks sent:", [block["type"] for block in message["content"]])
    response = get_llm_client().chat.completions.create(
        model=get_settings().chat_model, messages=[message]
    )
    print(f"\nQ: {question}\nA: {response.choices[0].message.content}")
    print(f"\nprompt_tokens={response.usage.prompt_tokens} (two images cost about twice one)")


if __name__ == "__main__":
    main()
