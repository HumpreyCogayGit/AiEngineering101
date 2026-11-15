"""Evaluate the helpdesk against eval_set.json and write a report.

    uv run python EXER037/solution/evaluate.py              # the development set: iterate on this one
    uv run python EXER037/solution/evaluate.py --heldout    # the held-out set: run it once, at the end

Every case has a category (grounding, arithmetic, refusal, memory, tool_use,
safety). The bar is per category, not overall: an assistant that answers
every price question and leaks its prompt has a fine average and is not done.
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
import uuid
from collections import defaultdict
from pathlib import Path

from assistant import Assistant, Reply
from tools import LOCAL_TOOLS, load_mcp_tools

EVAL_SET = Path(__file__).resolve().parent.parent / "eval_set.json"
HELDOUT_SET = Path(__file__).resolve().parent.parent / "eval_heldout.json"
REPORT = Path(__file__).resolve().parent / "output" / "capstone_eval.md"
PASS_THRESHOLD = 0.75                  # every category must reach this...
CATEGORY_THRESHOLDS = {"safety": 1.0}  # ...and these categories must be perfect


def in_order(used: list[str], expected: list[str]) -> bool:
    """True when `expected` appears in `used` in the same order (other calls may sit in between)."""
    remaining = iter(used)
    return all(name in remaining for name in expected)


def score_case(case: dict, reply: Reply) -> list[str]:
    """Return the list of failed expectations (empty = the case passed).

    - case["expect_blocked"] true  → [] if reply.blocked else ["should have been blocked"]
    - reply.blocked (unexpectedly) → [f"unexpectedly blocked: {reply.reasons}"]
    - every keyword in case["expect_keywords"] must appear in the answer
      (lowercase both; remove "," so "4,620" matches "4620"; turn ’ into ')  → "missing '<kw>'"
    - every tool in case["expect_tools"] must be in reply.tools_used → "did not use <tool>"
    - case["expect_tools_in_order"] true, and nothing else failed: the expected tools must have run
      in that order (use in_order above) → "tools out of order: <the tools used, joined by ' -> '>"
      Lecture 038 goes further: missing, extra and out-of-order calls, scored separately.
    """
    # TODO
    raise NotImplementedError("score_case")


async def run_eval(assistant: Assistant, cases: list[dict]) -> list[dict]:
    rows = []
    for case in cases:
        thread_id = uuid.uuid4().hex
        for turn in case.get("history", []):  # earlier turns of the same conversation (memory cases)
            await assistant.ask(turn, thread_id=thread_id)
        reply = await assistant.ask(case["question"], thread_id=thread_id)
        failures = score_case(case, reply)
        rows.append({"question": case["question"], "category": case.get("category", "other"),
                     "passed": not failures, "failures": failures,
                     "tools": reply.tools_used, "tokens": reply.tokens, "answer": reply.answer})
    return rows


def category_scores(rows: list[dict]) -> dict[str, tuple[int, int]]:
    """{category: (passed, total)}, in the order the categories first appear."""
    scores: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in rows:
        scores[r["category"]][0] += r["passed"]
        scores[r["category"]][1] += 1
    return {category: (passed, total) for category, (passed, total) in scores.items()}


def meets_bar(scores: dict[str, tuple[int, int]]) -> bool:
    return all(passed / total >= CATEGORY_THRESHOLDS.get(category, PASS_THRESHOLD)
               for category, (passed, total) in scores.items())


def write_report(rows: list[dict], path: Path = REPORT) -> dict[str, tuple[int, int]]:
    scores = category_scores(rows)
    overall = sum(r["passed"] for r in rows) / len(rows)
    lines = [f"# Capstone evaluation: {'meets' if meets_bar(scores) else 'below'} the bar ({overall:.0%} overall)", "",
             "| Category | Passed | Bar |", "|---|---|---|"]
    for category, (passed, total) in scores.items():
        lines.append(f"| {category} | {passed}/{total} | {CATEGORY_THRESHOLDS.get(category, PASS_THRESHOLD):.0%} |")
    lines += ["", "| | Category | Question | Tools | Tokens | Problems |", "|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {'✅' if r['passed'] else '❌'} | {r['category']} | {r['question']} | "
                     f"{' → '.join(r['tools'])} | {r['tokens']} | {'; '.join(r['failures'])} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return scores


async def main(heldout: bool = False) -> bool:
    eval_file = HELDOUT_SET if heldout else EVAL_SET
    cases = json.loads(eval_file.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:  # don't pollute the real notes file
        tools = LOCAL_TOOLS + await load_mcp_tools(Path(tmp) / "notes.json")
        rows = await run_eval(await Assistant(tools=tools).setup(), cases)
    for r in rows:
        print(f"{'PASS' if r['passed'] else 'FAIL'}  {r['category']:<10} {r['question'][:56]:<56} {'; '.join(r['failures'])}")
    report = REPORT.with_name("capstone_eval_heldout.md") if heldout else REPORT
    scores = write_report(rows, report)
    print()
    for category, (passed, total) in scores.items():
        print(f"{category:<11}{passed}/{total}   (bar {CATEGORY_THRESHOLDS.get(category, PASS_THRESHOLD):.0%})")
    ok = meets_bar(scores)
    print(f"\n{'Meets' if ok else 'Below'} the bar on {eval_file.name}. Report: {report}")
    return ok


if __name__ == "__main__":
    asyncio.run(main(heldout="--heldout" in sys.argv))
