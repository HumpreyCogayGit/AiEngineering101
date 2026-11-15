"""EXER046 stretch goal 2 — tool-call reliability per model, with the EXER038 scorer (EXER038).

    AICOURSE_COMPARE_MODELS="a,b" uv run python EXER046/stretch/goal2_trajectories_per_model.py

The suite in this lesson checks the FIRST tool a model picks. An agent needs
more: the right tools, in the right order, across several steps. EXER038 built
a scorer for that. Here the capstone assistant runs on every candidate, three
multi-step questions each, and its trajectories are scored for missing calls,
extra calls and order.

A cheaper model that picks the first tool well can still skip the calculator
on the third step. This is where that shows.
"""

from __future__ import annotations

import asyncio
import tempfile
import uuid
from pathlib import Path

from aicourse.stretch import solution_module, solution_path

base = solution_module(__file__, "routing.py")
trajectory = solution_module(__file__, "trajectory_eval.py", exercise="EXER038")
solution_path(__file__, exercise="EXER037")
import assistant as capstone  # noqa: E402
import tools as capstone_tools  # noqa: E402

CASES = [
    {"question": "What does 3 bags of Barako Bold plus one Hand Grinder Pro cost in total?",
     "expected": ["search_knowledge_base", "calculator"]},
    {"question": "How much do 2 bags of Decaf Cloud and a Cold Brew Bottle cost together?",
     "expected": ["search_knowledge_base", "calculator"]},
    {"question": "Look up the express shipping fee and save it as a note titled 'Express'.",
     "expected": ["search_knowledge_base", "notes_add_note"]},
]


async def score(candidate) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tools = capstone_tools.LOCAL_TOOLS + await capstone_tools.load_mcp_tools(Path(tmp) / "notes.json")
        helpdesk = await capstone.Assistant(llm=candidate.chat_model(temperature=0), tools=tools).setup()
        passed = 0
        for case in CASES:
            reply = await helpdesk.ask(case["question"], uuid.uuid4().hex)
            missing, extra = trajectory.missing_and_extra(reply.tools_used, case["expected"])
            ordered = trajectory.in_order(reply.tools_used, case["expected"])
            ok = not missing and ordered
            passed += ok
            print(f"  {'PASS' if ok else 'FAIL'} {candidate.name:<22} {' -> '.join(reply.tools_used) or '(none)'}"
                  + (f"   missing {missing}" if missing else ""))
        return passed


async def main() -> None:
    totals = {}
    for candidate in base.candidates_from_env():
        totals[candidate.name] = await score(candidate)
    print()
    for name, passed in totals.items():
        print(f"{name:<22} {passed}/{len(CASES)} trajectories right")


if __name__ == "__main__":
    asyncio.run(main())
