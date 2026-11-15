"""EXER024 stretch goal 1 — calibrate the judge: against itself, and against a person.

    uv run python EXER024/stretch/goal1_judge_calibration.py

A judge you have never compared with a human is an opinion, not a metric.
human_labels.json holds 18 answers to Nimbus questions, each scored 1-5 for
faithfulness and correctness by the course author. They are written to hit the
places judges slip: answers that are right but short, right but chatty,
mostly right with one invented detail, wrong refusals and right refusals.

The script grades every answer TWICE with the solution's judge and reports:

- self-agreement   how often the judge gives the same score twice. This is noise.
- exact agreement  how often the judge's first score equals the human score.
- adjacent         how often it is within one point. A 1-5 scale has fuzzy edges,
                   so "4 vs 5" is a weaker signal than "1 vs 5".
- by kind          where the disagreements are. A judge that misses invented
                   details is not safe to use for faithfulness, whatever its average.

A judge that agrees with itself every time can still disagree with you every time:
repeatability is not accuracy.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "evaluate.py")
LABELS = Path(__file__).resolve().parent / "human_labels.json"
METRICS = ("faithfulness", "correctness")


def grade(judge_llm, item: dict, metric: str) -> int:
    if metric == "faithfulness":
        return base.judge_faithfulness(judge_llm, item["question"], item["context"], item["answer"]).score
    return base.judge_correctness(judge_llm, item["question"], item["reference"], item["answer"]).score


def agreement(pairs: list[tuple[int, int]]) -> tuple[float, float]:
    """(exact, adjacent) agreement as fractions, for (judge, human) score pairs."""
    exact = sum(a == b for a, b in pairs) / len(pairs)
    adjacent = sum(abs(a - b) <= 1 for a, b in pairs) / len(pairs)
    return exact, adjacent


def report(rows: list[dict]) -> str:
    lines = []
    for metric in METRICS:
        first = [(r[metric][0], r["human"][metric]) for r in rows]
        self_same = sum(r[metric][0] == r[metric][1] for r in rows) / len(rows)
        exact, adjacent = agreement(first)
        lines.append(f"{metric:<13} self-agreement {self_same:>4.0%}   vs human: exact {exact:>4.0%}, "
                     f"within one point {adjacent:>4.0%}")
        by_kind: dict[str, list[int]] = defaultdict(list)
        for r in rows:
            by_kind[r["kind"]].append(abs(r[metric][0] - r["human"][metric]))
        worst = sorted(by_kind.items(), key=lambda kv: -sum(kv[1]) / len(kv[1]))
        lines.append("              mean gap by kind: " + ", ".join(
            f"{kind} {sum(gaps) / len(gaps):.1f}" for kind, gaps in worst))
    return "\n".join(lines)


def main() -> None:
    items = json.loads(LABELS.read_text(encoding="utf-8"))
    judge_llm = get_chat_model(temperature=0)
    rows = []
    for i, item in enumerate(items, 1):
        scores = {m: [grade(judge_llm, item, m) for _ in range(2)] for m in METRICS}
        rows.append({**item, **scores})
        human = item["human"]
        flag = "  <- off by 2+" if any(abs(scores[m][0] - human[m]) >= 2 for m in METRICS) else ""
        print(f"[{i:>2}/{len(items)}] {item['kind']:<13} faithful judge={scores['faithfulness']} human={human['faithfulness']}"
              f"   correct judge={scores['correctness']} human={human['correctness']}{flag}")
    print("\n" + report(rows))
    print("\nChange the rubric in evaluate.py or the judge model, run again, and compare. "
          "Trust the judge for a metric only where it agrees with the human labels.")


if __name__ == "__main__":
    main()
