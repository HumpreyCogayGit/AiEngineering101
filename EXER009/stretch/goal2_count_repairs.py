"""EXER009 stretch goal 2 — how often is the repair loop needed?

    uv run python EXER009/stretch/goal2_count_repairs.py          # 20 runs
    uv run python EXER009/stretch/goal2_count_repairs.py 6        # fewer runs

parse_with_repair() hides its retries: you get a valid object either way.
Counting the model calls per run makes them visible. Half the runs use the
exercise's precise prompt, half a vague one that never names the keys, so you
can see what a clear instruction is worth in calls (= money and latency).
"""

from __future__ import annotations

import sys
from collections import Counter

from aicourse.llm import get_llm_client
from aicourse.stretch import solution_module

base = solution_module(__file__, "formatting.py")

VAGUE_SYSTEM = "Extract the event from the user's text as JSON."


class CountingClient:
    """Passes every call through to the real client, and counts them."""

    def __init__(self, client) -> None:
        self._client = client
        self.calls = 0
        self.chat = self  # so that client.chat.completions.create(...) lands here
        self.completions = self

    def create(self, **kwargs):
        self.calls += 1
        return self._client.chat.completions.create(**kwargs)


def calls_needed(client, system: str) -> int | None:
    """Model calls used by one parse_with_repair run (None = it gave up)."""
    counting = CountingClient(client)
    messages = [{"role": "system", "content": system}, {"role": "user", "content": base.SAMPLE_EMAIL}]
    try:
        base.parse_with_repair(counting, messages, base.Event, max_attempts=3)
    except ValueError:
        return None
    return counting.calls


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    client = get_llm_client()
    for label, system in (("precise prompt", base.JSON_MODE_SYSTEM), ("vague prompt", VAGUE_SYSTEM)):
        results = Counter(calls_needed(client, system) for _ in range(runs // 2))
        repaired = sum(n for calls, n in results.items() if calls is None or calls > 1)
        print(f"{label:<15} {runs // 2} runs: repair needed in {repaired}")
        for calls, n in sorted(results.items(), key=lambda item: (item[0] is None, item[0] or 0)):
            print(f"    {'gave up after 3 calls' if calls is None else f'{calls} model call(s)':<24} x{n}")


if __name__ == "__main__":
    main()
