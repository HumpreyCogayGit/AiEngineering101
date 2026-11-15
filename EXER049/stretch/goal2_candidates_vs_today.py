"""EXER049 stretch goal 2 — run the new cases against today's assistant, before they enter the gate (EXER048).

    uv run python EXER049/stretch/goal2_candidates_vs_today.py

The candidates came from failures in production traces. Before they join the
evaluation set, run them against the assistant as it is now:

- a case that FAILS today is a regression test for a live bug: fix the bug,
  then add the case, re-record and approve a new baseline (EXER048)
- a case that PASSES today was fixed already (or the production failure came
  from a version that is gone): it still joins the set, so the bug cannot return

Either way the evaluation set grows from what customers actually asked.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from aicourse.stretch import solution_module, solution_path

base = solution_module(__file__, "feedback_loop.py")
solution_path(__file__, exercise="EXER037")
import assistant as capstone  # noqa: E402
import evaluate  # noqa: E402
import tools as capstone_tools  # noqa: E402


def candidates() -> list[dict]:
    traces = {t["trace_id"]: t for t in base.load_traces()}
    reviews = json.loads(base.REVIEWS.read_text(encoding="utf-8"))
    cases = [c for c in (base.to_eval_case(traces[i], r) for i, r in reviews.items()) if c]
    return base.dedupe(cases, json.loads(base.CAPSTONE_EVAL.read_text(encoding="utf-8")))


async def main() -> None:
    cases = candidates()
    with tempfile.TemporaryDirectory() as tmp:
        tools = capstone_tools.LOCAL_TOOLS + await capstone_tools.load_mcp_tools(Path(tmp) / "notes.json")
        rows = await evaluate.run_eval(await capstone.Assistant(tools=tools).setup(), cases)
    for case, row in zip(cases, rows):
        state = "passes today" if row["passed"] else "FAILS today"
        print(f"{state:<13} {case['source']:<17} {case['question'][:44]:<44} {'; '.join(row['failures'])}")
    failing = sum(not r["passed"] for r in rows)
    print(f"\n{len(cases)} new cases: {failing} fail today (live bugs), {len(cases) - failing} pass (guards against a return).")
    print("Next: add them to EXER037/eval_set.json, then `release_gate.py record` and `approve` (EXER048).")


if __name__ == "__main__":
    asyncio.run(main())
