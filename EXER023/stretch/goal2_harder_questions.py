"""EXER023 stretch goal 2 — five harder questions that separate the strategies at @4.

    uv run python EXER023/stretch/goal2_harder_questions.py

On the 19 standard questions nearly every strategy scores 100% at @4, so that
column measures nothing. hard_questions.json adds five questions chosen to
hit known weaknesses: paraphrases with no shared keywords (bad for BM25),
exact phrases among many similar chunks (bad for vectors), and a question
that needs world knowledge. Each one says why it is hard.

The file is kept separate from data/eval_questions.json, which other
exercises and their checks rely on. Scores depend on your embedding model:
the point is that the @4 column now discriminates, not the exact numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

from aicourse.settings import DATA_DIR
from aicourse.stretch import solution_module

base = solution_module(__file__, "better_retrieval.py")

HARD = Path(__file__).resolve().parent / "hard_questions.json"
NEEDS_LLM = {"multi-query", "hybrid+rerank"}


def rank_of(retrieve, row: dict, k: int = 4) -> str:
    sources = [d.metadata.get("source") for d in retrieve(row["question"])[:k]]
    return str(sources.index(row["expected_source"]) + 1) if row["expected_source"] in sources else "-"


def main() -> None:
    standard = json.loads((DATA_DIR / "eval_questions.json").read_text(encoding="utf-8"))
    hard = json.loads(HARD.read_text(encoding="utf-8"))
    retrievers = {n: r for n, r in base.build_retrievers().items() if n not in NEEDS_LLM}

    print(f"Hit rate @4            {'standard (19)':>14} {'hard (5)':>9} {'all (24)':>9}")
    for name, retrieve in retrievers.items():
        print(f"  {name:<20} {base.hit_rate(retrieve, standard):>14.0%} {base.hit_rate(retrieve, hard):>9.0%} "
              f"{base.hit_rate(retrieve, standard + hard):>9.0%}")

    print("\nRank of the right document for each hard question (- = not in the top 4):")
    print(f"  {'':<46}" + "".join(f"{n:>8}" for n in retrievers))
    for row in hard:
        print(f"  {row['question']:<46}" + "".join(f"{rank_of(r, row):>8}" for r in retrievers.values()))
        print(f"      {row['why_hard']}")


if __name__ == "__main__":
    main()
