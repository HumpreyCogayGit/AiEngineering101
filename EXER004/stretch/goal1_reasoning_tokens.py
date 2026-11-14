"""EXER004 stretch goal 1 — report reasoning tokens when the model has them.

    uv run python EXER004/stretch/goal1_reasoning_tokens.py

A reasoning model spends output tokens on thinking before it writes. They are
part of `completion_tokens` (and of the bill) but not of the text. The count
is in `usage.completion_tokens_details.reasoning_tokens`, and not every
provider or model sends that field, so read it defensively.
"""

from __future__ import annotations

from dataclasses import dataclass

from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "sdk_basics.py")


@dataclass
class DetailedResult(base.CompletionResult):
    reasoning_tokens: int | None = None  # None = the model did not report it

    @property
    def visible_tokens(self) -> int:
        """Output tokens that became text you can read."""
        return self.completion_tokens - (self.reasoning_tokens or 0)


def reasoning_tokens_of(usage) -> int | None:
    details = getattr(usage, "completion_tokens_details", None)
    return getattr(details, "reasoning_tokens", None)


def ask(client, prompt: str, max_tokens: int | None = None) -> DetailedResult:
    kwargs = {get_settings().max_tokens_param: max_tokens} if max_tokens is not None else {}
    response = client.chat.completions.create(
        model=get_settings().chat_model, messages=[{"role": "user", "content": prompt}], **kwargs
    )
    choice = response.choices[0]
    return DetailedResult(
        text=choice.message.content or "",
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        finish_reason=choice.finish_reason,
        reasoning_tokens=reasoning_tokens_of(response.usage),
    )


def main() -> None:
    result = ask(base.make_client(), "Which is heavier: 3 kg of feathers or 2 kg of steel? One sentence.")
    print(result.text)
    print(f"\ncompletion_tokens={result.completion_tokens}  finish={result.finish_reason}")
    if result.reasoning_tokens is None:
        print("reasoning_tokens : not reported by this model")
    else:
        print(f"reasoning_tokens : {result.reasoning_tokens}  (hidden thinking, billed as output)")
        print(f"visible tokens   : {result.visible_tokens}")


if __name__ == "__main__":
    main()
