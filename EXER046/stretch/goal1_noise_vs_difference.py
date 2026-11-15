"""EXER046 stretch goal 1 — is the difference between two models bigger than the noise?

    AICOURSE_COMPARE_MODELS="a,b" uv run python EXER046/stretch/goal1_noise_vs_difference.py [runs]

One run of a 16-case suite is a small sample. Run it three times and the same
model can score 0.75 once and 1.0 the next time on a four-case task. Before you
switch models because one scored higher, check that the gap between them is
larger than the spread of each model against itself.

For every candidate the suite runs `runs` times (default 3). The script prints
each task's accuracy per run, its spread (max - min), and for each task whether
the gap between the candidates' means exceeds the larger of their spreads.
"""

from __future__ import annotations

import statistics
import sys

from aicourse.stretch import solution_module

base = solution_module(__file__, "routing.py")


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    cases = base.suite()
    results: dict[str, dict[str, list[float]]] = {}
    for candidate in base.candidates_from_env():
        llm = candidate.chat_model(temperature=0)
        per_task: dict[str, list[float]] = {}
        for _ in range(runs):
            summary = base.summarize([base.run_case(llm, case) for case in cases], None)
            for task, accuracy in summary["accuracy"].items():
                per_task.setdefault(task, []).append(accuracy)
        results[candidate.name] = per_task
        for task, values in per_task.items():
            print(f"{candidate.name:<22} {task:<9} runs {values}  spread {max(values) - min(values):.2f}")
    names = list(results)
    if len(names) < 2:
        print("\nOne candidate only: the spread above is the noise any comparison must beat. "
              "Set AICOURSE_COMPARE_MODELS to compare two.")
        return
    a, b = names[0], names[-1]
    print()
    for task in results[a]:
        gap = abs(statistics.mean(results[a][task]) - statistics.mean(results[b][task]))
        noise = max(max(v) - min(v) for v in (results[a][task], results[b][task]))
        verdict = "no difference" if gap == 0 else ("a real difference" if gap > noise else "within the noise")
        print(f"{task:<9} {a} vs {b}: gap {gap:.2f}, noise {noise:.2f} -> {verdict}")


if __name__ == "__main__":
    main()
