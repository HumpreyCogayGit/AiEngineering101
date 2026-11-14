"""EXER024 stretch goal 1 — does the judge agree with itself?

    uv run python EXER024/stretch/goal1_judge_consistency.py         # first 8 questions
    uv run python EXER024/stretch/goal1_judge_consistency.py 19      # all answerable questions

An LLM judge is a model call, so it can give two different scores to the
same answer. Each answer here is generated ONCE and graded TWICE on both
metrics. Where the two grades differ, the difference is noise in your
metric: a change in the report smaller than that noise means nothing.
"""

from __future__ import annotations

import json
import sys

from aicourse.llm import get_chat_model
from aicourse.rag import build_rag_chain, format_docs
from aicourse.settings import DATA_DIR
from aicourse.stretch import solution_module

base = solution_module(__file__, "evaluate.py")


def grade_twice(chain, judge_llm, row: dict) -> dict:
    result = chain.invoke(row["question"])  # one answer...
    context, answer = format_docs(result["docs"]), result["answer"]
    return {                                 # ...graded twice per metric
        "question": row["question"],
        "faithfulness": [base.judge_faithfulness(judge_llm, row["question"], context, answer).score
                         for _ in range(2)],
        "correctness": [base.judge_correctness(judge_llm, row["question"], row["reference_answer"], answer).score
                        for _ in range(2)],
    }


def disagreement(rows: list[dict], metric: str) -> tuple[int, int]:
    """(how many rows got two different scores, the largest gap)."""
    gaps = [abs(r[metric][0] - r[metric][1]) for r in rows]
    return sum(g > 0 for g in gaps), max(gaps)


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    dataset = json.loads((DATA_DIR / "eval_questions.json").read_text(encoding="utf-8"))
    dataset = [r for r in dataset if r["expected_source"]][:limit]
    chain, judge_llm = build_rag_chain(), get_chat_model(temperature=0)
    rows = []
    for i, row in enumerate(dataset, 1):
        rows.append(grade_twice(chain, judge_llm, row))
        r = rows[-1]
        flag = "  <- differs" if len(set(r["faithfulness"])) > 1 or len(set(r["correctness"])) > 1 else ""
        print(f"[{i}/{len(dataset)}] faithful={r['faithfulness']} correct={r['correctness']}{flag}  {r['question'][:50]}")
    print()
    for metric in ("faithfulness", "correctness"):
        count, gap = disagreement(rows, metric)
        print(f"{metric:<13} the judge disagreed with itself on {count} of {len(rows)} answers "
              f"({count / len(rows):.0%}); largest gap: {gap} point(s)")
    print("\nA model that only accepts the default temperature cannot be made more repeatable with temperature=0.")


if __name__ == "__main__":
    main()
