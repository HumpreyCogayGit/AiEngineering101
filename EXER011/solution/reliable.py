"""EXER011 — Reliability (reference solution).

Real APIs fail: rate limits (429), timeouts, network blips, server errors (5xx).
A production client retries the *temporary* failures with exponential backoff,
fails fast on permanent ones, logs what happened, and runs calls concurrently
without overwhelming the API.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Awaitable, Callable, TypeVar

import openai

from aicourse.llm import get_async_openai_client, get_openai_client
from aicourse.settings import get_settings

log = logging.getLogger("reliable")
T = TypeVar("T")

# Temporary problems — worth retrying.
RETRYABLE = (
    openai.RateLimitError,         # 429
    openai.APITimeoutError,        # request took too long
    openai.APIConnectionError,     # network problem
    openai.InternalServerError,    # 5xx
)


def backoff_delay(attempt: int, base_delay: float = 0.5, max_delay: float = 20.0) -> float:
    """Exponential backoff with jitter: ~base, 2*base, 4*base, ... (+ up to 25% random)."""
    delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
    return delay + random.uniform(0, delay * 0.25)


def call_with_retry(
    fn: Callable[[], T],
    max_attempts: int = 4,
    base_delay: float = 0.5,
    retry_on: tuple[type[BaseException], ...] = RETRYABLE,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call fn(); on a retryable error wait and try again, up to max_attempts total."""
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retry_on as exc:
            if attempt == max_attempts:
                log.error("giving up after %d attempts: %s", attempt, exc)
                raise
            delay = backoff_delay(attempt, base_delay)
            log.warning("attempt %d failed (%s); retrying in %.2fs", attempt, type(exc).__name__, delay)
            sleep(delay)
    raise AssertionError("unreachable")


class ReliableClient:
    """Wraps the SDK client: disables the SDK's own retries (we do it ourselves) and logs every call."""

    def __init__(self, client=None, max_attempts: int = 4) -> None:
        self.client = client or get_openai_client().with_options(max_retries=0)
        self.max_attempts = max_attempts

    def complete(self, messages: list[dict], **kwargs) -> str:
        start = time.perf_counter()
        response = call_with_retry(
            lambda: self.client.chat.completions.create(
                model=get_settings().chat_deployment, messages=messages, **kwargs
            ),
            max_attempts=self.max_attempts,
        )
        log.info(
            "completion ok in %.2fs, tokens=%s",
            time.perf_counter() - start,
            getattr(response.usage, "total_tokens", "?"),
        )
        return response.choices[0].message.content or ""


async def complete_many(
    prompts: list[str],
    concurrency: int = 3,
    complete_one: Callable[[str], Awaitable[str]] | None = None,
) -> list[str]:
    """Run many prompts concurrently, at most `concurrency` at a time, results in input order."""
    if complete_one is None:
        client = get_async_openai_client()

        async def complete_one(prompt: str) -> str:
            response = await client.chat.completions.create(
                model=get_settings().chat_deployment,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""

    semaphore = asyncio.Semaphore(concurrency)

    async def limited(prompt: str) -> str:
        async with semaphore:
            return await complete_one(prompt)

    return await asyncio.gather(*(limited(p) for p in prompts))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    # 1. Retry demo with a function that fails twice.
    attempts = {"n": 0}

    def flaky():
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise openai.APIConnectionError(request=None)  # type: ignore[arg-type]
        return "success on attempt 3"

    print(call_with_retry(flaky, base_delay=0.2))

    # 2. A logged, retried real call.
    print(ReliableClient().complete([{"role": "user", "content": "Say hi in 3 languages."}]))

    # 3. Concurrency: 6 prompts, 3 at a time.
    countries = ["Japan", "Kenya", "Peru", "Norway", "Vietnam", "Chile"]
    start = time.perf_counter()
    answers = asyncio.run(complete_many([f"Capital of {c}? One word." for c in countries], concurrency=3))
    print(f"\n{len(answers)} answers in {time.perf_counter() - start:.1f}s:")
    for c, a in zip(countries, answers):
        print(f"  {c}: {a}")


if __name__ == "__main__":
    main()
