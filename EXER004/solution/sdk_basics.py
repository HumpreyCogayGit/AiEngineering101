"""EXER004 — The SDK and Model Parameters (reference solution)."""

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
    """Create an OpenAI SDK client that talks to your Azure resource."""
    s = get_settings()
    return OpenAI(
        base_url=s.base_url,
        api_key=s.api_key.get_secret_value(),
        timeout=s.request_timeout,
    )


def ask(
    client: OpenAI,
    prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> CompletionResult:
    """Send one user message and return the text, token usage and finish reason."""
    # Optional parameters are only sent when you set them, so the model's own
    # defaults apply otherwise. That matters: not every model accepts every parameter.
    kwargs = {}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_completion_tokens"] = max_tokens
    response = client.chat.completions.create(
        model=get_settings().chat_deployment,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    choice = response.choices[0]
    return CompletionResult(
        text=choice.message.content or "",
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        finish_reason=choice.finish_reason,
    )


def count_tokens(text: str) -> int:
    """Count tokens locally with the o200k_base encoding used by GPT-4o / GPT-4.1 models."""
    encoding = tiktoken.get_encoding("o200k_base")
    return len(encoding.encode(text))


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    input_price_per_1m: float,
    output_price_per_1m: float,
) -> float:
    """Cost in dollars. Prices are quoted per 1 million tokens."""
    return (
        prompt_tokens * input_price_per_1m / 1_000_000
        + completion_tokens * output_price_per_1m / 1_000_000
    )


def temperature_experiment(
    client: OpenAI, prompt: str, temperatures: list[float], runs: int = 3
) -> dict[float, list[str]]:
    """Ask the same prompt `runs` times at each temperature and collect the answers.

    A temperature the model rejects (reasoning models such as the gpt-5 family
    only accept the default, 1) gets an empty list instead of crashing the run.
    """
    results: dict[float, list[str]] = {}
    for t in temperatures:
        try:
            results[t] = [ask(client, prompt, temperature=t).text for _ in range(runs)]
        except BadRequestError as exc:
            if "temperature" not in str(exc):
                raise
            results[t] = []
    return results


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
