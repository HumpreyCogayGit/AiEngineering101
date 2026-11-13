"""EXER011 checks (offline). Run:  uv run python EXER011/check.py"""

import asyncio

import httpx
import openai

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("reliable.py")


def rate_limit_error():
    response = httpx.Response(429, request=httpx.Request("POST", "https://example.com"))
    return openai.RateLimitError("rate limited", response=response, body=None)


@checker.check("backoff_delay() doubles each attempt (with <= 25% jitter)")
def _():
    for attempt, base in [(1, 0.5), (2, 1.0), (3, 2.0), (4, 4.0)]:
        d = mod.backoff_delay(attempt, 0.5)
        assert base <= d <= base * 1.25, f"attempt {attempt}: {d}"
    assert mod.backoff_delay(20, 0.5, max_delay=10) <= 12.5


@checker.check("call_with_retry() retries a 429 and then succeeds")
def _():
    calls, sleeps = [], []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise rate_limit_error()
        return "ok"

    assert mod.call_with_retry(flaky, sleep=sleeps.append) == "ok"
    assert len(calls) == 3 and len(sleeps) == 2, (len(calls), sleeps)
    assert sleeps[1] > sleeps[0], "delays should grow"


@checker.check("call_with_retry() gives up after max_attempts and re-raises")
def _():
    calls = []

    def always_fails():
        calls.append(1)
        raise rate_limit_error()

    try:
        mod.call_with_retry(always_fails, max_attempts=3, sleep=lambda s: None)
    except openai.RateLimitError:
        assert len(calls) == 3, len(calls)
        return
    raise AssertionError("expected RateLimitError")


@checker.check("call_with_retry() does NOT retry permanent errors")
def _():
    calls = []

    def bad_request():
        calls.append(1)
        raise ValueError("bad input")

    try:
        mod.call_with_retry(bad_request, sleep=lambda s: None)
    except ValueError:
        assert len(calls) == 1, "a permanent error must fail on the first attempt"
        return
    raise AssertionError("expected ValueError")


@checker.check("complete_many() respects the concurrency limit and keeps order")
def _():
    state = {"running": 0, "peak": 0}

    async def fake_one(prompt):
        state["running"] += 1
        state["peak"] = max(state["peak"], state["running"])
        await asyncio.sleep(0.05 if prompt != "p0" else 0.15)  # first one is slowest
        state["running"] -= 1
        return prompt.upper()

    prompts = [f"p{i}" for i in range(7)]
    out = asyncio.run(mod.complete_many(prompts, concurrency=3, complete_one=fake_one))
    assert out == [p.upper() for p in prompts], out
    assert state["peak"] == 3, f"peak concurrency was {state['peak']}"


checker.run()
