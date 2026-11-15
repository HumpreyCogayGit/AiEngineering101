"""EXER048 stretch goal 2 — gate the tool trajectories too (EXER038).

    uv run python EXER048/stretch/goal2_trajectory_category.py      # offline: uses the recordings

The capstone's categories score answers, and since EXER037 they check that the
expected tools ran (in order, where a case asks for it). What they cannot see
is a release that keeps every answer right but gets there with far more tool
calls: four searches where one did, a cost and latency regression.

This script adds a "trajectory" category computed from the recorded replies
with EXER038's missing_and_extra() and in_order(): a case passes when nothing
is missing, the order holds, and there is at most one extra call (a second
lookup is often reasonable, EXER038). Then it plays a regression: the same
answers, with three grounding questions searching four times each. The answer
categories pass; the trajectory category catches it.
"""

from __future__ import annotations

import asyncio
import copy
import json

from aicourse.stretch import solution_module

gate = solution_module(__file__, "release_gate.py")
trajectory = solution_module(__file__, "trajectory_eval.py", exercise="EXER038")


def trajectory_results(replies: dict[str, dict]) -> dict:
    cases = [c for c in json.loads(gate.evaluate.EVAL_SET.read_text(encoding="utf-8")) if c.get("expect_tools")]
    passed = 0
    for case in cases:
        used = replies[case["question"]]["tools_used"]
        missing, extra = trajectory.missing_and_extra(used, case["expect_tools"])
        passed += not missing and trajectory.in_order(used, case["expect_tools"]) and len(extra) <= 1
    return {"passed": passed, "total": len(cases)}


async def results_with_trajectory(replies: dict[str, dict]) -> dict:
    rows = await gate.run(gate.Replayer(replies))
    return {**gate.results_from_rows(rows), "trajectory": trajectory_results(replies)}


async def main() -> None:
    recorded = json.loads(gate.RECORDINGS.read_text(encoding="utf-8"))
    baseline = json.loads(gate.BASELINE.read_text(encoding="utf-8"))
    baseline["results"] = await results_with_trajectory(recorded["replies"])  # the same recordings, one more category

    regressed = copy.deepcopy(recorded["replies"])
    for question in ("Is the Maginhawa café open on Mondays?", "How many vacation days do full-time employees get?",
                     "When do loyalty stars expire?"):
        regressed[question]["tools_used"] = ["search_knowledge_base"] * 4  # same answer, four searches
    current = await results_with_trajectory(regressed)

    for label, results in (("same recordings", baseline["results"]), ("regressed", current)):
        passed, report = gate.gate(baseline, baseline["release"], results)
        print(f"--- {label}: {'PASSED' if passed else 'FAILED'}")
        print("\n".join(line for line in report.splitlines() if line.startswith(("| grounding", "| trajectory"))))
    print("\nEvery answer is still right, so grounding passes; the trajectory gate fails on the extra searches. "
          "Answers and trajectories are two views, and each catches a regression the other misses.")


if __name__ == "__main__":
    asyncio.run(main())
