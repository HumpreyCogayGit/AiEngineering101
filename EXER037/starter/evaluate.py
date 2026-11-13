"""Evaluate the helpdesk against eval_set.json and write a report.

    uv run python EXER037/solution/evaluate.py
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import uuid
from pathlib import Path

from assistant import Assistant, Reply
from tools import LOCAL_TOOLS, load_mcp_tools

EVAL_SET = Path(__file__).resolve().parent.parent / "eval_set.json"
REPORT = Path(__file__).resolve().parent / "output" / "capstone_eval.md"
PASS_THRESHOLD = 0.8


def score_case(case: dict, reply: Reply) -> list[str]:
    """Return the list of failed expectations (empty = the case passed)."""
    """
    - case["expect_blocked"] true  → [] if reply.blocked else ["should have been blocked"]
    - reply.blocked (unexpectedly) → [f"unexpectedly blocked: {reply.reasons}"]
    - every keyword in case["expect_keywords"] must appear in the answer
      (lowercase both; remove "," so "4,620" matches "4620"; turn ’ into ')  → "missing '<kw>'"
    - every tool in case["expect_tools"] must be in reply.tools_used → "did not use <tool>"
    """
    # TODO
    raise NotImplementedError("score_case")


async def run_eval(assistant: Assistant, cases: list[dict]) -> list[dict]:
    rows = []
    for case in cases:
        reply = await assistant.ask(case["question"], thread_id=uuid.uuid4().hex)
        failures = score_case(case, reply)
        rows.append({"question": case["question"], "passed": not failures, "failures": failures,
                     "tools": reply.tools_used, "tokens": reply.tokens, "answer": reply.answer})
    return rows


def write_report(rows: list[dict]) -> float:
    rate = sum(r["passed"] for r in rows) / len(rows)
    lines = [f"# Capstone evaluation — {rate:.0%} passed", "",
             "| | Question | Tools | Tokens | Problems |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {'✅' if r['passed'] else '❌'} | {r['question']} | {', '.join(r['tools'])} | "
                     f"{r['tokens']} | {'; '.join(r['failures'])} |")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rate


async def main() -> bool:
    cases = json.loads(EVAL_SET.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:  # don't pollute the real notes file
        tools = LOCAL_TOOLS + await load_mcp_tools(Path(tmp) / "notes.json")
        rows = await run_eval(await Assistant(tools=tools).setup(), cases)
    for r in rows:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['question'][:60]:<60} {'; '.join(r['failures'])}")
    rate = write_report(rows)
    print(f"\n{rate:.0%} passed (threshold {PASS_THRESHOLD:.0%}). Report: {REPORT}")
    return rate >= PASS_THRESHOLD


if __name__ == "__main__":
    asyncio.run(main())
