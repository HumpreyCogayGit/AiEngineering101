"""EXER038 stretch goal 1 — efficiency: redundant calls and wasted steps.

    uv run python EXER038/stretch/goal1_efficiency.py      # offline: three hand-written trajectories

A trajectory can be correct and still wasteful: the same lookup twice, or
five calls where two were enough. Every extra call is latency and tokens.
Two numbers make that visible:

    redundant calls   calls that repeat an earlier call exactly (same tool, same arguments)
    efficiency        expected number of calls / actual number of calls (1.0 = no waste)
"""

from __future__ import annotations

import json

from aicourse.stretch import solution_module

base = solution_module(__file__, "trajectory_eval.py")
Call = base.Call


def redundant_calls(actual: list) -> list:
    """Calls whose tool and arguments were already used earlier in the same run."""
    seen: set[str] = set()
    repeated = []
    for call in actual:
        key = call.name + json.dumps(call.args, sort_keys=True, default=str).lower()
        if key in seen:
            repeated.append(call)
        seen.add(key)
    return repeated


def efficiency(actual: list, expected: list) -> float:
    """1.0 when the agent used no more calls than expected; lower with every extra call."""
    if not actual:
        return 1.0 if not expected else 0.0
    return min(1.0, len(expected) / len(actual))


def score(actual: list, expected: list) -> dict:
    result = base.score_trajectory(actual, expected)
    repeats = redundant_calls(actual)
    result["efficiency"] = round(efficiency(actual, expected), 2)
    result["problems"] += [f"redundant call: {c.name}({c.args})" for c in repeats]
    return result


def main() -> None:
    expected = [Call("lookup_product", {"name": "Barako Bold"}), Call("calculator", {"expression": {"evaluates_to": 780}})]
    runs = {
        "direct": [Call("lookup_product", {"name": "Barako Bold"}), Call("calculator", {"expression": "2 * 390"})],
        "double-checks": [Call("lookup_product", {"name": "Barako Bold"}), Call("lookup_product", {"name": "Barako Bold"}),
                          Call("calculator", {"expression": "2 * 390"}), Call("calculator", {"expression": "390 + 390"})],
        "wanders": [Call("store_hours", {"branch": "BGC"}), Call("lookup_product", {"name": "Barako Bold"}),
                    Call("lookup_product", {"name": "Decaf Cloud"}), Call("calculator", {"expression": "2 * 390"})],
    }
    print(f"{'run':<15}{'tools':<7}{'order':<7}{'args':<7}{'efficiency':<12}problems")
    for name, actual in runs.items():
        s = score(actual, expected)
        print(f"{name:<15}{str(s['tools']):<7}{str(s['order']):<7}{str(s['arguments']):<7}{s['efficiency']:<12}"
              f"{'; '.join(s['problems']) or '-'}")
    print("\nAll three runs reach the right answer. Only the first one is the run you want to pay for.")


if __name__ == "__main__":
    main()
