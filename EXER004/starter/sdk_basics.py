"""EXER004 — The SDK and Model Parameters.

Replace the raw HTTP of EXER003 with the official `openai` SDK, then
experiment with parameters, tokens and cost. Complete every TODO, then run:

    uv run python EXER004/starter/sdk_basics.py
    uv run python EXER004/check.py
"""

from __future__ import annotations

from dataclasses import dataclass

import tiktoken
from openai import BadRequestError, OpenAI

from aicourse.settings import get_settings


@dataclass
class CompletionResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


def make_client() -> OpenAI:
    """Create an OpenAI SDK client that talks to your Azure resource.

    Hint: OpenAI(base_url=s.base_url, api_key=s.api_key.get_secret_value(), timeout=s.request_timeout)
    where s = get_settings(). The v1 base URL makes Azure look exactly like OpenAI.
    """
    # TODO
    raise NotImplementedError("make_client")


def ask(
    client: OpenAI,
    prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> CompletionResult:
    """Send one user message and return a CompletionResult.

    - model = get_settings().chat_deployment
    - ONLY when temperature is not None, pass `temperature=temperature`
    - ONLY when max_tokens is not None, pass it as `max_completion_tokens=max_tokens`
    - read: response.choices[0].message.content, response.choices[0].finish_reason,
            response.usage.prompt_tokens, response.usage.completion_tokens
    """
    # TODO
    raise NotImplementedError("ask")


def count_tokens(text: str) -> int:
    """Count tokens locally with tiktoken's "o200k_base" encoding.

    Hint: tiktoken.get_encoding("o200k_base").encode(text) returns a list of token ids.
    """
    # TODO
    raise NotImplementedError("count_tokens")


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    input_price_per_1m: float,
    output_price_per_1m: float,
) -> float:
    """Cost in dollars. Prices are quoted per 1 MILLION tokens."""
    # TODO
    raise NotImplementedError("estimate_cost")


def temperature_experiment(
    client: OpenAI, prompt: str, temperatures: list[float], runs: int = 3
) -> dict[float, list[str]]:
    """Ask the same prompt `runs` times at each temperature.

    Return {temperature: [answer1, answer2, ...]}.

    Not every model accepts every temperature: reasoning models (gpt-5 family,
    o-series) only accept the default and raise BadRequestError otherwise.
    Catch BadRequestError for a temperature and store an EMPTY list for it
    (re-raise if "temperature" is not in str(error): that is a different bug).
    """
    # TODO
    raise NotImplementedError("temperature_experiment")


def main() -> None:
    client = make_client()

    result = ask(client, "Explain tokens to a 10-year-old in two sentences.")
    print(result.text)
    print(f"\nprompt={result.prompt_tokens} completion={result.completion_tokens} "
          f"finish={result.finish_reason}")
    # Example prices (USD per 1M tokens) — check the Azure pricing page for yours.
    print(f"Estimated cost: ${estimate_cost(result.prompt_tokens, result.completion_tokens, 0.40, 1.60):.6f}")

    print("\nLocal token count of the prompt:", count_tokens("Explain tokens to a 10-year-old in two sentences."))

    cut = ask(client, "Write a long story about a dragon.", max_tokens=5)
    print(f"\nWith max_tokens=5 -> {cut.text!r}  finish_reason={cut.finish_reason}")

    print("\n--- Temperature experiment ---")
    results = temperature_experiment(client, "Invent a name for a coffee shop. Reply with the name only.", [0.0, 1.0])
    for temp, answers in results.items():
        print(f"temperature={temp}: {answers or 'not supported by this model'}")


if __name__ == "__main__":
    main()
