"""EXER035 stretch goal 1 — latency percentiles (p50, p95) per tool.

    uv run python EXER035/stretch/goal1_latency_percentiles.py      # offline: simulated tools

An average hides the slow calls, and the slow calls are what users remember.
Percentiles describe the spread:

    p50  half of the calls were faster than this (the typical call)
    p95  only 1 call in 20 was slower (the bad-day call)

The tracker already stores every span, so this is a new report, not new
instrumentation. The demo calls two simulated tools 40 times each with the
tracker attached, the same way an agent run would.
"""

from __future__ import annotations

import random
import time
from collections import defaultdict

from langchain_core.tools import tool

from aicourse.stretch import solution_module

base = solution_module(__file__, "observability.py")


def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile: the smallest value that at least p% of the values do not exceed."""
    ordered = sorted(values)
    rank = max(1, -(-len(ordered) * p // 100))  # ceil(n * p / 100), at least 1
    return ordered[int(rank) - 1]


class LatencyTracker(base.UsageTracker):
    def tool_latency(self) -> dict[str, dict]:
        """{tool name: {"calls", "errors", "mean", "p50", "p95", "max"}} in seconds."""
        by_tool: dict[str, list] = defaultdict(list)
        for span in self.spans.values():
            if span.kind == "tool" and span.end is not None:
                by_tool[span.name].append(span)
        report = {}
        for name, spans in by_tool.items():
            durations = [s.duration for s in spans]
            report[name] = {
                "calls": len(spans),
                "errors": sum(1 for s in spans if s.error),
                "mean": sum(durations) / len(durations),
                "p50": percentile(durations, 50),
                "p95": percentile(durations, 95),
                "max": max(durations),
            }
        return report


@tool
def search_kb(query: str) -> str:
    """A simulated knowledge-base search: steady, about 20 ms."""
    time.sleep(random.uniform(0.015, 0.025))
    return "passages"


@tool
def inventory(product: str) -> str:
    """A simulated inventory service: usually 10 ms, but 1 call in 10 takes 300 ms."""
    time.sleep(0.3 if random.random() < 0.1 else random.uniform(0.008, 0.012))
    return "12 bags"


def main() -> None:
    random.seed(7)  # the same "slow" calls on every run
    tracker = LatencyTracker()
    for i in range(40):
        search_kb.invoke({"query": f"q{i}"}, {"callbacks": [tracker]})
        inventory.invoke({"product": f"p{i}"}, {"callbacks": [tracker]})

    print(f"{'tool':<12}{'calls':>6}{'mean':>9}{'p50':>9}{'p95':>9}{'max':>9}")
    for name, row in tracker.tool_latency().items():
        print(f"{name:<12}{row['calls']:>6}" + "".join(f"{row[k] * 1000:>7.0f}ms" for k in ("mean", "p50", "p95", "max")))
    print("\ninventory has the better p50 and the worse p95: the mean alone would hide both facts.")


if __name__ == "__main__":
    main()
