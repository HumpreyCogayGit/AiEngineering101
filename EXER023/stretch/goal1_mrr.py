"""EXER023 stretch goal 1 — MRR beside hit rate.

    uv run python EXER023/stretch/goal1_mrr.py            # the four strategies that need no LLM
    uv run python EXER023/stretch/goal1_mrr.py --all      # also multi-query and rerank (slower, costs calls)

Hit rate @4 only asks "is the right document in the top 4?". It cannot tell
rank 1 from rank 4. MRR (mean reciprocal rank) can: each question scores
1/position of the first correct result (1, 0.5, 0.33, 0.25, or 0 for a miss),
and MRR is the average. Two strategies with the same hit rate can differ in
MRR, and the one that ranks the answer higher puts it where the model reads first.
"""

from __future__ import annotations

import json
import sys

from aicourse.settings import DATA_DIR
from aicourse.stretch import solution_module

base = solution_module(__file__, "better_retrieval.py")

NEEDS_LLM = {"multi-query", "hybrid+rerank"}


def reciprocal_rank(sources: list[str], expected: str) -> float:
    """1/position of the first result from the expected source; 0.0 when it is absent."""
    for position, source in enumerate(sources, start=1):
        if source == expected:
            return 1.0 / position
    return 0.0


def mrr(retrieve, dataset: list[dict], k: int = 4) -> float:
    rows = [r for r in dataset if r.get("expected_source")]
    return sum(
        reciprocal_rank([d.metadata.get("source") for d in retrieve(r["question"])[:k]], r["expected_source"])
        for r in rows
    ) / len(rows)


def main() -> None:
    dataset = json.loads((DATA_DIR / "eval_questions.json").read_text(encoding="utf-8"))
    questions = [r["question"] for r in dataset if r["expected_source"]]
    print(f"{len(questions)} questions\n")
    print(f"  {'strategy':<14} {'hit@1':>6} {'hit@4':>6} {'MRR@4':>6}")
    for name, retrieve in base.build_retrievers().items():
        if name in NEEDS_LLM and "--all" not in sys.argv:
            continue
        results = {q: retrieve(q) for q in questions}  # retrieve once, score three ways
        cached = results.__getitem__
        print(f"  {name:<14} {base.hit_rate(cached, dataset, k=1):>6.0%} "
              f"{base.hit_rate(cached, dataset, k=4):>6.0%} {mrr(cached, dataset):>6.2f}")
    print("\nMRR falls between hit@1 and hit@4: it rewards a hit, and rewards it more the higher it ranks.")


if __name__ == "__main__":
    main()
