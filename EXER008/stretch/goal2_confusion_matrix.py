"""EXER008 stretch goal 2 — a confusion matrix, not only accuracy.

    uv run python EXER008/stretch/goal2_confusion_matrix.py

Accuracy says HOW OFTEN the classifier is wrong. A confusion matrix says
HOW: which label is mistaken for which. "account tickets end up in billing"
tells you which definition to sharpen; "81%" does not.

Rows are the expected label, columns are what the model answered.
"""

from __future__ import annotations

from collections import Counter

from aicourse.llm import get_llm_client
from aicourse.stretch import solution_module

base = solution_module(__file__, "prompts.py")

COLUMNS = base.LABELS + ["unknown"]


def confusion(client, builder, dataset: list[dict]) -> Counter:
    """Count (expected, predicted) pairs."""
    return Counter((row["label"], base.classify(client, builder(row["text"]))) for row in dataset)


def print_matrix(counts: Counter) -> None:
    print(f"{'expected / predicted':<22}" + "".join(f"{c:>11}" for c in COLUMNS))
    for expected in base.LABELS:
        cells = "".join(f"{counts[(expected, predicted)] or '.':>11}" for predicted in COLUMNS)
        print(f"{expected:<22}{cells}")
    total = sum(counts.values())
    right = sum(n for (expected, predicted), n in counts.items() if expected == predicted)
    print(f"accuracy = {right}/{total} = {right / total:.0%}")


def main() -> None:
    client = get_llm_client()
    data = base.load_dataset()
    for name, builder in (("v1 naive", base.build_messages_v1), ("v3 few-shot", base.build_messages_v3)):
        print(f"\n--- {name} ---")
        print_matrix(confusion(client, builder, data))
    print("\nRead it by row: off-diagonal numbers are the mistakes, and their column says what they became.")


if __name__ == "__main__":
    main()
