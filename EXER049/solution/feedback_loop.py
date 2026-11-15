"""EXER049 — Learning from Production (reference solution).

    uv run python EXER049/solution/feedback_loop.py       # offline: four weeks of traces -> review queue, drift, new cases

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
    """{trace_id: [signals]} for answers the customer's NEXT message in the same thread complained about.

    - "asked for a person": the next message asks for a human, an agent or a person
    - "asked again": the next message comes within `window_seconds` and shares at least one content
      word (longer than 3 letters) with the question: the customer is trying again in other words
    """
    by_thread: dict[str, list[dict]] = defaultdict(list)
    for trace in sorted(traces, key=lambda t: t["at"]):
        by_thread[trace["thread_id"]].append(trace)
    signals: dict[str, list[str]] = {}
    for thread in by_thread.values():
        for current, following in zip(thread, thread[1:]):
            found = []
            if HUMAN_REQUEST.search(following["question"]):
                found.append("asked for a person")
            else:
                gap = (datetime.fromisoformat(following["at"]) - datetime.fromisoformat(current["at"])).total_seconds()
                shared = {w for w in words(current["question"]) & words(following["question"]) if len(w) > 3}
                if gap <= window_seconds and shared:
                    found.append("asked again")
            if found:
                signals[current["trace_id"]] = found
    return signals


# ------------------------------------------------------------------ 2. what a person should look at
def sample_for_review(traces: list[dict], signals: dict[str, list[str]], random_k: int, seed: int = 0) -> list[dict]:
    """Every thumbs-down, every trace with an implicit signal, then `random_k` random others.

    Each picked trace gets a "why" field. Blocked requests are left out (the guardrail report covers
    them), and so are the follow-up messages themselves ("Can I talk to a human?" is a signal, not a
    failure of its own). Same seed, same sample: two reviewers see the same queue.
    """
    followups = {t["trace_id"] for t in traces if HUMAN_REQUEST.search(t["question"])}
    eligible = [t for t in traces if not t["blocked"] and t["trace_id"] not in followups]
    flagged = []
    for trace in eligible:
        why = (["thumbs down"] if trace.get("feedback") == "down" else []) + signals.get(trace["trace_id"], [])
        if why:
            flagged.append({**trace, "why": why})
    flagged_ids = {t["trace_id"] for t in flagged}
    rest = [t for t in eligible if t["trace_id"] not in flagged_ids]
    picked = random.Random(seed).sample(rest, min(random_k, len(rest)))
    return flagged + [{**t, "why": ["random sample"]} for t in sorted(picked, key=lambda t: t["at"])]


# ------------------------------------------------------------------ 3. from a reviewed failure to a test
def normalize(question: str) -> str:
    return re.sub(r"\s+", " ", question).strip().lower().rstrip("?!. ")


def to_eval_case(trace: dict, review: dict) -> dict | None:
    """A capstone evaluation case (EXER037 format) from a trace a person reviewed. None if it was fine."""
    if review.get("verdict") != "fail":
        return None
    return {"category": review["category"], "question": trace["question"],
            "expect_keywords": review.get("expect_keywords", []), "expect_tools": review.get("expect_tools", []),
            "source": f"production:{trace['trace_id']}"}


def dedupe(cases: list[dict], existing: list[dict]) -> list[dict]:
    """Drop cases whose normalized question is already in `existing` or earlier in `cases`."""
    seen = {normalize(c["question"]) for c in existing}
    out = []
    for case in cases:
        key = normalize(case["question"])
        if key not in seen:
            seen.add(key)
            out.append(case)
    return out


# ------------------------------------------------------------------ 4. drift
def weekly_metrics(traces: list[dict]) -> dict[str, dict]:
    """Per ISO week ("2026-W43"), over answered (not blocked) traces:
    questions, rated, thumbs_down_rate (of rated), refusal_rate, mean_tokens, p95_seconds."""
    weeks: dict[str, list[dict]] = defaultdict(list)
    for trace in traces:
        if not trace["blocked"]:
            year, week, _ = datetime.fromisoformat(trace["at"]).isocalendar()
            weeks[f"{year}-W{week:02d}"].append(trace)
    out = {}
    for week, items in sorted(weeks.items()):
        rated = [t for t in items if t.get("feedback")]
        seconds = sorted(t["seconds"] for t in items)
        out[week] = {
            "questions": len(items),
            "rated": len(rated),
            "thumbs_down_rate": round(sum(t["feedback"] == "down" for t in rated) / len(rated), 3) if rated else 0.0,
            "refusal_rate": round(sum(any(r in t["answer"].lower().replace("’", "'") for r in REFUSAL)
                                      for t in items) / len(items), 3),
            "mean_tokens": round(statistics.mean(t["tokens"] for t in items)),
            "p95_seconds": seconds[max(0, -(-95 * len(seconds) // 100) - 1)],
        }
    return out


def drift_alerts(metrics: dict[str, dict], watch: dict[str, float]) -> list[str]:
    """Compare each week with the mean of ALL earlier weeks. `watch` maps a metric to the relative
    increase that raises an alert (0.5 = 50% above the earlier mean). A metric whose earlier mean
    is 0 alerts when it becomes positive."""
    alerts = []
    weeks = list(metrics)
    for i, week in enumerate(weeks[1:], start=1):
        for metric, limit in watch.items():
            before = statistics.mean(metrics[w][metric] for w in weeks[:i])
            now = metrics[week][metric]
            if (before == 0 and now > 0) or (before > 0 and now > before * (1 + limit)):
                alerts.append(f"{week}: {metric} {now} vs {before:.3g} before")
    return alerts


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
