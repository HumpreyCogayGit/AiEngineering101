"""EXER024 stretch goal 2 — evaluate the best EXER023 retriever and compare reports.

    uv run python EXER024/stretch/goal2_compare_retrievers.py         # first 8 questions
    uv run python EXER024/stretch/goal2_compare_retrievers.py 20      # the whole golden set

EXER023 ranked retrievers by hit rate. That says nothing about the ANSWERS.
Here the same evaluation runs twice, changing one thing only: the retriever
(plain vector search vs hybrid search). Two reports, one table. Only now can
you say whether better retrieval bought better answers.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from langchain_core.runnables import RunnableLambda

from aicourse.llm import get_chat_model
from aicourse.rag import build_rag_chain
from aicourse.settings import DATA_DIR
from aicourse.stretch import solution_module

base = solution_module(__file__, "evaluate.py")
retrieval = solution_module(__file__, "better_retrieval.py", exercise="EXER023")

OUTPUT = Path(__file__).resolve().parent / "output"


def run_evaluation(name: str, chain, judge_llm, dataset: list[dict]) -> dict:
    rows = []
    for i, row in enumerate(dataset, 1):
        print(f"  [{name} {i}/{len(dataset)}] {row['question'][:60]}")
        rows.append(base.evaluate_row(chain, judge_llm, row))
    summary = base.summarize(rows)
    base.write_report(rows, summary, OUTPUT / f"eval_report_{name}.md")
    return summary


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    dataset = json.loads((DATA_DIR / "eval_questions.json").read_text(encoding="utf-8"))
    dataset = dataset[: limit - 1] + dataset[-1:]  # always keep the unanswerable question
    judge_llm = get_chat_model(temperature=0)
    hybrid = RunnableLambda(retrieval.build_retrievers(k=4)["hybrid"])  # a function becomes a retriever step

    summaries = {
        "vector": run_evaluation("vector", build_rag_chain(), judge_llm, dataset),
        "hybrid": run_evaluation("hybrid", build_rag_chain(retriever=hybrid), judge_llm, dataset),
    }
    print(f"\n{'metric':<14}{'vector':>8}{'hybrid':>8}{'change':>8}")
    for metric in ("hit_rate", "mrr", "faithfulness", "correctness", "refusal_rate"):
        a, b = summaries["vector"][metric], summaries["hybrid"][metric]
        print(f"{metric:<14}{a:>8.2f}{b:>8.2f}{b - a:>+8.2f}")
    print(f"\nReports: {OUTPUT.relative_to(OUTPUT.parents[2])}/eval_report_vector.md and eval_report_hybrid.md")
    print("One question moves a rate by several points on a set this small: read the rows, not only the averages.")


if __name__ == "__main__":
    main()
