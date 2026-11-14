"""EXER011 stretch goal 1 — a circuit breaker.

    uv run python EXER011/stretch/goal1_circuit_breaker.py      # offline: a simulated outage

Retries help with a blip. In an outage they make things worse: every request
waits through all its retries and then fails anyway. A circuit breaker counts
consecutive failures and, past a limit, stops calling for a while and fails
immediately instead.

    closed     normal: calls go through
    open       after N failures in a row: calls fail at once, nothing is sent
    half-open  after the cool-down: ONE trial call; success closes, failure reopens
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

import openai

from aicourse.stretch import solution_module

base = solution_module(__file__, "reliable.py")
T = TypeVar("T")


class CircuitOpenError(RuntimeError):
    """Raised instead of calling the API while the circuit is open."""


class CircuitBreaker:
    def __init__(self, max_failures: int = 3, reset_after: float = 30.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.max_failures = max_failures
        self.reset_after = reset_after
        self.clock = clock  # injected, like `sleep` in the exercise, so tests need not wait
        self.failures = 0
        self.opened_at: float | None = None

    @property
    def state(self) -> str:
        if self.opened_at is None:
            return "closed"
        return "half-open" if self.clock() - self.opened_at >= self.reset_after else "open"

    def call(self, fn: Callable[[], T]) -> T:
        if self.state == "open":
            wait = self.reset_after - (self.clock() - self.opened_at)
            raise CircuitOpenError(f"circuit open: not calling for another {wait:.0f}s")
        try:
            result = fn()
        except base.RETRYABLE:
            self.failures += 1
            if self.failures >= self.max_failures:
                self.opened_at = self.clock()  # (re)open: a failed trial call restarts the cool-down
            raise
        self.failures, self.opened_at = 0, None  # success closes the circuit
        return result


def main() -> None:
    now = {"t": 0.0}
    breaker = CircuitBreaker(max_failures=3, reset_after=30, clock=lambda: now["t"])
    sent = {"n": 0}
    outage = {"on": True}

    def call_api() -> str:
        sent["n"] += 1
        if outage["on"]:
            raise openai.APIConnectionError(request=None)  # type: ignore[arg-type]
        return "ok"

    def attempt(label: str) -> None:
        try:
            # The breaker wraps the retrying call: one "failure" = retries exhausted.
            result = breaker.call(lambda: base.call_with_retry(call_api, max_attempts=2, sleep=lambda s: None))
        except CircuitOpenError as exc:
            result = f"FAILED FAST ({exc})"
        except base.RETRYABLE as exc:
            result = f"failed after retries ({type(exc).__name__})"
        print(f"t={now['t']:>3.0f}s {label:<28} -> {result:<52} state={breaker.state:<9} requests sent={sent['n']}")

    for i in range(1, 6):
        attempt(f"request {i} (outage)")
        now["t"] += 1
    now["t"] = 40
    outage["on"] = False
    attempt("request 6 (service is back)")
    attempt("request 7")
    print("\nRequests 4 and 5 sent nothing: the breaker spared the struggling service and the user's time.")


if __name__ == "__main__":
    import logging

    logging.getLogger("reliable").setLevel(logging.CRITICAL)  # the retry warnings would drown the table
    main()
