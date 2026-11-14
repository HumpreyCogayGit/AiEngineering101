"""EXER038 stretch goal 2 — score the trajectories of the capstone assistant (EXER037).

    uv run python EXER038/stretch/goal2_score_capstone.py

The capstone's own evaluation checks `expect_tools` as a SET: was each tool
used at all? Your scorer says more. Here the EXER037 assistant answers three
questions, and its tool calls are scored for missing and extra calls and for
order: the price must be looked up BEFORE the calculator can add it up.

`Reply.tools_used` holds the tool names in the order they ran, which is all
that missing_and_extra() and in_order() need.
"""

from __future__ import annotations

import asyncio
import tempfile
import uuid
from pathlib import Path

from aicourse.stretch import solution_module, solution_path

base = solution_module(__file__, "trajectory_eval.py")
solution_path(__file__, exercise="EXER037")
import assistant as assistant_module  # noqa: E402
import tools as tools_module  # noqa: E402

CASES = [
    {"question": "How many days do I have to return unopened beans?", "expected": ["search_knowledge_base"]},
    {"question": "What does 3 bags of Barako Bold plus one Hand Grinder Pro cost in total?",
     "expected": ["search_knowledge_base", "calculator"]},
    {"question": "Please save a note titled 'Cold brew' saying: steep 16 to 18 hours.", "expected": ["notes_add_note"]},
]


async def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tools = tools_module.LOCAL_TOOLS + await tools_module.load_mcp_tools(Path(tmp) / "notes.json")
        helpdesk = await assistant_module.Assistant(tools=tools).setup()
        for case in CASES:
            reply = await helpdesk.ask(case["question"], thread_id=uuid.uuid4().hex)
            missing, extra = base.missing_and_extra(reply.tools_used, case["expected"])
            ordered = base.in_order(reply.tools_used, case["expected"])
            verdict = "PASS" if not missing and ordered else "FAIL"
            print(f"{verdict}  {case['question'][:60]}")
            print(f"      trajectory: {' -> '.join(reply.tools_used) or '(no tools)'}")
            print(f"      missing: {missing or '-'}   extra: {extra or '-'}   in order: {ordered}")
    print("\nAn extra search is not a failure here: a second lookup is cheap and often right. "
          "A missing or late one is.")


if __name__ == "__main__":
    asyncio.run(main())
