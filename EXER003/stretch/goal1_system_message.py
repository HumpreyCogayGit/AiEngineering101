"""EXER003 stretch goal 1 — add a system message and compare token usage.

    uv run python EXER003/stretch/goal1_system_message.py

The system message is part of the request, so it is counted (and billed) as
input on EVERY call. Send the same question with and without one and compare
`usage.prompt_tokens`.
"""

from __future__ import annotations

import httpx

from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "raw_call.py")

SYSTEM = "You are a patient teacher. Answer in one short sentence, without jargon."


def send(messages: list[dict]) -> dict:
    s = get_settings()
    response = httpx.post(
        base.build_url(s.base_url),
        headers=base.build_headers(s.api_key.get_secret_value()),
        json={"model": s.chat_model, "messages": messages},
        timeout=s.request_timeout,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    question = {"role": "user", "content": "What is a large language model?"}
    plain = send([question])
    with_system = send([{"role": "system", "content": SYSTEM}, question])
    for label, data in (("without system", plain), ("with system", with_system)):
        usage = data["usage"]
        print(f"{label:<15} prompt_tokens={usage['prompt_tokens']:<4} completion_tokens={usage['completion_tokens']}")
        print(f"{'':<15} {data['choices'][0]['message']['content'][:110]}")
    extra = with_system["usage"]["prompt_tokens"] - plain["usage"]["prompt_tokens"]
    print(f"\nThe system message costs {extra} extra input tokens, on every request that carries it.")


if __name__ == "__main__":
    main()
