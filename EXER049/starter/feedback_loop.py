"""EXER049 — Learning from Production (starter).

    uv run python EXER049/starter/feedback_loop.py       # offline: four weeks of traces -> review queue, drift, new cases

The evaluation set was written by hand before launch. Once customers arrive,
they ask what nobody thought of, and the assistant fails in ways no case
covers. This lesson closes the loop:

    traces + feedback --> signals --> a sample to review --> reviewed failures --> new eval cases
                                                                                   (into the EXER048 gate)
                     --> weekly metrics --> drift alerts

Thumbs down is the obvious signal and the rarest: most customers never rate.
Implicit signals (asking again in other words within a minute, asking for a
person) are far more common. A random sample of the rest finds the failures
nobody flagged at all.
"""

from __future__ import annotations

import json
import random
import re
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
TRACES = HERE / "traces.jsonl"
REVIEWS = HERE / "reviews.json"
CANDIDATES = Path(__file__).resolve().parent / "output" / "eval_candidates.json"
CAPSTONE_EVAL = HERE.parent / "EXER037" / "eval_set.json"

HUMAN_REQUEST = re.compile(r"\b(human|person|agent|someone real|real person|representative)\b", re.I)
REFUSAL = ("don't know", "do not know", "isn't in the nimbus documents")


def load_traces(path: Path = TRACES) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


# ------------------------------------------------------------------ 1. implicit signals
def implicit_signals(traces: list[dict], window_seconds: int = 60) -> dict[str, list[str]]:
    """{trace_id: [signals]} for answers that the customer's NEXT message in the same thread complained about.

    Group the traces by thread_id (sorted by "at"), then look at each pair (current, following):
    - HUMAN_REQUEST.search(following["question"])             -> ["asked for a person"]
    - otherwise: the gap in seconds (datetime.fromisoformat on both "at") <= window_seconds, AND the two
      questions share at least one content word longer than 3 letters (use words())  -> ["asked again"]
    Only traces with a signal appear in the result.
    """
    # TODO
    raise NotImplementedError("implicit_signals")


# ------------------------------------------------------------------ 2. what a person should look at
def sample_for_review(traces: list[dict], signals: dict[str, list[str]], random_k: int, seed: int = 0) -> list[dict]:
    """The review queue: flagged traces first, then `random_k` random others, each with a "why" list.

    - Leave out blocked traces, and the "talk to a human" messages themselves (HUMAN_REQUEST matches the
      question): they are signals about the PREVIOUS answer, not answers to review.
    - Flagged: why = ["thumbs down"] if feedback == "down", plus signals.get(trace_id, []). Keep the ones
      with a non-empty why, in their original order, as {**trace, "why": why}.
    - Random: random.Random(seed).sample(the rest, min(random_k, len(rest))), sorted by "at", each with
      why ["random sample"]. A fixed seed means two reviewers see the same queue.
    """
    # TODO
    raise NotImplementedError("sample_for_review")


# ------------------------------------------------------------------ 3. from a reviewed failure to a test
def normalize(question: str) -> str:
    return re.sub(r"\s+", " ", question).strip().lower().rstrip("?!. ")


def to_eval_case(trace: dict, review: dict) -> dict | None:
    """A capstone evaluation case from a reviewed trace, or None when review["verdict"] != "fail".

    {"category": review["category"], "question": trace["question"],
     "expect_keywords": review.get("expect_keywords", []), "expect_tools": review.get("expect_tools", []),
     "source": f"production:{trace['trace_id']}"}       # where the case came from, for later
    """
    # TODO
    raise NotImplementedError("to_eval_case")


def dedupe(cases: list[dict], existing: list[dict]) -> list[dict]:
    """Drop cases whose normalize(question) is already in `existing`, or earlier in `cases`. Keep the order."""
    # TODO
    raise NotImplementedError("dedupe")


# ------------------------------------------------------------------ 4. drift
def weekly_metrics(traces: list[dict]) -> dict[str, dict]:
    """Per ISO week ("2026-W43": year, week from datetime.fromisoformat(at).isocalendar()), over the
    traces that were NOT blocked, sorted by week:

      questions          how many
      rated              how many have a feedback value
      thumbs_down_rate   share of the RATED ones that are "down" (0.0 when none rated), rounded to 3
      refusal_rate       share whose answer contains one of REFUSAL (lowercase; turn ’ into '), rounded to 3
      mean_tokens        round(mean of tokens)
      p95_seconds        nearest-rank p95 of seconds (as in EXER044)
    """
    # TODO
    raise NotImplementedError("weekly_metrics")


def drift_alerts(metrics: dict[str, dict], watch: dict[str, float]) -> list[str]:
    """Compare every week (from the second on) with the MEAN of all earlier weeks, for each metric in
    `watch` ({metric: allowed relative increase}).

    Alert when the earlier mean is 0 and the week's value is above 0, or when the value is above
    mean * (1 + limit). The alert text: f"{week}: {metric} {now} vs {before:.3g} before".
    """
    # TODO
    raise NotImplementedError("drift_alerts")


# ------------------------------------------------------------------ demo (given)
def main() -> None:
    traces = load_traces()
    signals = implicit_signals(traces)
    queue = sample_for_review(traces, signals, random_k=10, seed=49)
    rated = sum(1 for t in traces if t.get("feedback"))
    print(f"{len(traces)} traces, {rated} rated, {sum(t.get('feedback') == 'down' for t in traces)} thumbs down, "
          f"{len(signals)} with an implicit signal")
    print(f"review queue: {len(queue)} traces")
    for trace in queue[:8]:
        print(f"  {trace['trace_id']} {', '.join(trace['why']):<32} {trace['question'][:44]:<44} -> {trace['answer'][:40]}")

    reviews = json.loads(REVIEWS.read_text(encoding="utf-8"))  # what a person decided for the queue
    by_id = {t["trace_id"]: t for t in traces}
    cases = [c for c in (to_eval_case(by_id[i], r) for i, r in reviews.items() if i in by_id) if c]
    existing = json.loads(CAPSTONE_EVAL.read_text(encoding="utf-8"))
    new = dedupe(cases, existing)
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\n{len(cases)} reviewed failures -> {len(new)} new evaluation cases (after removing duplicates) "
          f"in {CANDIDATES.name}")

    metrics = weekly_metrics(traces)
    print("\nweek       questions  thumbs-down  refusals  p95 s")
    for week, m in metrics.items():
        print(f"{week}  {m['questions']:>9}  {m['thumbs_down_rate']:>11.0%}  {m['refusal_rate']:>8.0%}  {m['p95_seconds']:>5}")
    for alert in drift_alerts(metrics, {"refusal_rate": 0.5, "p95_seconds": 0.3}):
        print("ALERT", alert)


if __name__ == "__main__":
    main()
