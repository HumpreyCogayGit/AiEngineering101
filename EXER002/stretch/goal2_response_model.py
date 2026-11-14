"""EXER002 stretch goal 2 — a Pydantic model of the whole response.

    uv run python EXER002/stretch/goal2_response_model.py

Instead of chaining ["choices"][0]["message"]["content"] and hoping, describe
the response once. Validation then tells you exactly which part is malformed,
and your editor completes `.choices[0].message.content`.

Models nest: a field's type can be another model, or a list of them.
"""

from __future__ import annotations

from pydantic import BaseModel, ValidationError

from aicourse.stretch import solution_module

base = solution_module(__file__, "primer.py")


class ReplyMessage(BaseModel):
    role: str
    content: str | None  # None when the model answers with a tool call


class Choice(BaseModel):
    index: int
    message: ReplyMessage
    finish_reason: str


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatResponse(BaseModel):
    """Only the fields we use. Pydantic ignores the others (e.g. provider-specific extras)."""

    id: str
    model: str
    choices: list[Choice]
    usage: Usage


def main() -> None:
    response = ChatResponse.model_validate(base.load_response(base.SAMPLE))
    print("Reply       :", response.choices[0].message.content)
    print("Tokens used :", response.usage.total_tokens)
    print("Finish      :", response.choices[0].finish_reason)
    try:
        ChatResponse.model_validate({"id": "x", "model": "m", "choices": [{"index": 0}], "usage": {}})
    except ValidationError as exc:
        print(f"\nA malformed response gives {exc.error_count()} precise errors:")
        for error in exc.errors():
            print("  ", ".".join(str(part) for part in error["loc"]), "->", error["msg"])


if __name__ == "__main__":
    main()
