"""EXER031 stretch goal 2 — count model calls and tokens: supervisor vs handoff (EXER035).

    uv run python EXER031/stretch/goal2_count_calls.py

The lecture claims the supervisor needs "5 or more" model calls where the
handoff team needs 3. Measure it. The UsageTracker from EXER035 is a callback
handler, so it sees every model call of every nested agent: pass it once in
the run config and it counts the whole team.
"""

from __future__ import annotations

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "team.py")
observability = solution_module(__file__, "observability.py", exercise="EXER035")


def measure(graph, request: str) -> tuple[dict, list[str]]:
    tracker = observability.UsageTracker()
    result = graph.invoke({"messages": [("user", request)]}, {"callbacks": [tracker]})
    return tracker.report(), result["steps"]


def main() -> None:
    llm = get_chat_model(temperature=0)
    request = ("Customer email: 'Hi! My grinder arrived broken yesterday, and I also wonder if I can "
               "bring my dog when I pick up a replacement at your café?'")
    reports = {}
    for name, build in (("supervisor", base.build_team), ("handoff", base.build_handoff_team)):
        reports[name], steps = measure(build(llm, base.kb_search), request)
        print(f"{name:<11} steps: {' -> '.join(steps)}")

    print(f"\n{'':<16}{'supervisor':>12}{'handoff':>10}")
    for key in ("llm_calls", "tool_calls", "input_tokens", "output_tokens", "llm_seconds"):
        print(f"{key:<16}{reports['supervisor'][key]:>12}{reports['handoff'][key]:>10}")
    print(f"{'cost_usd':<16}{reports['supervisor']['cost_usd']:>12.5f}{reports['handoff']['cost_usd']:>10.5f}")
    ratio = reports["supervisor"]["input_tokens"] / max(1, reports["handoff"]["input_tokens"])
    print(f"\nThe supervisor team read {ratio:.1f}x the input tokens: every routing decision re-reads the conversation.")


if __name__ == "__main__":
    main()
