"""EXER019 stretch goal 2 — the similarity matrix as a heat map.

    uv run python EXER019/stretch/goal2_similarity_heatmap.py
    open EXER019/stretch/output/similarity.html

Every sentence is compared with every other one. The picture shows what a
list of numbers hides: which sentences cluster. Nothing needs installing:
the heat map is an HTML table whose cell colour is the score, plus a
terminal version drawn with block characters.
"""

from __future__ import annotations

import html
from pathlib import Path

from aicourse.llm import get_llm_client
from aicourse.stretch import solution_module

base = solution_module(__file__, "embeddings.py")

OUTPUT = Path(__file__).resolve().parent / "output" / "similarity.html"
SHADES = " ░▒▓█"


def similarity_matrix(vectors: list[list[float]]) -> list[list[float]]:
    return [[base.cosine_similarity(a, b) for b in vectors] for a in vectors]


def scale(score: float, low: float, high: float) -> float:
    """Map a score to 0..1 between the weakest and strongest off-diagonal score."""
    return max(0.0, min(1.0, (score - low) / (high - low))) if high > low else 0.0


def off_diagonal_range(matrix: list[list[float]]) -> tuple[float, float]:
    scores = [s for i, row in enumerate(matrix) for j, s in enumerate(row) if i != j]
    return min(scores), max(scores)


def print_heatmap(matrix: list[list[float]]) -> None:
    low, high = off_diagonal_range(matrix)
    print("    " + "".join(f"{j + 1:^5}" for j in range(len(matrix))))
    for i, row in enumerate(matrix):
        cells = "".join(f" {SHADES[round(scale(s, low, high) * (len(SHADES) - 1))] * 3} " for s in row)
        print(f"{i + 1:>3} {cells}")


def write_html(texts: list[str], matrix: list[list[float]]) -> None:
    low, high = off_diagonal_range(matrix)
    head = "".join(f"<th>{j + 1}</th>" for j in range(len(texts)))
    rows = []
    for i, row in enumerate(matrix):
        cells = "".join(
            f'<td style="background:rgba(11,110,110,{scale(s, low, high):.2f})" title="{html.escape(texts[j])}">{s:.2f}</td>'
            for j, s in enumerate(row)
        )
        rows.append(f"<tr><th>{i + 1}</th>{cells}<td class='t'>{html.escape(texts[i])}</td></tr>")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        "<!doctype html><meta charset='utf-8'><title>Similarity heat map</title>"
        "<style>body{font:15px system-ui;margin:24px}table{border-collapse:collapse}"
        "td,th{padding:8px 10px;text-align:center;border:1px solid #ddd}.t{text-align:left;border:0}</style>"
        f"<h1>Cosine similarity between {len(texts)} sentences</h1>"
        f"<table><tr><th></th>{head}<th></th></tr>{''.join(rows)}</table>"
        "<p>Darker = more similar. The diagonal is each sentence with itself (1.00).</p>",
        encoding="utf-8",
    )


def main() -> None:
    vectors = base.embed_texts(get_llm_client(), base.CORPUS)
    matrix = similarity_matrix(vectors)
    for i, text in enumerate(base.CORPUS, 1):
        print(f"{i}. {text}")
    print()
    print_heatmap(matrix)
    _, a, b = max((s, i, j) for i, row in enumerate(matrix) for j, s in enumerate(row) if i < j)
    print(f"\nMost similar pair ({matrix[a][b]:.2f}): {a + 1} and {b + 1}")
    write_html(base.CORPUS, matrix)
    print(f"Heat map written to {OUTPUT.relative_to(OUTPUT.parents[3])}")


if __name__ == "__main__":
    main()
