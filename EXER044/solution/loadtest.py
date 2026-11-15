"""EXER044 — a local load test and its report (reference solution).

    uv run python EXER044/solution/loadtest.py

Starts the service in this process with a FAKE assistant (0.4 s per answer,
no model calls, nothing billed), and lets 16 simulated users talk to it over
real HTTP at the same time. Each user asks, waits for the answer, thinks for
0.1 s and asks again (a "closed loop"). The report is what users experienced:

    throughput            answered questions per second
    p50 / p95 / p99       latency of the answered questions
    by status             how many got 200, 429, 503, 504
    SLO                   the share of "good" requests, and how much error budget the run used

It runs twice, with 2 and with 8 concurrent slots, so you can see the
trade-off: fewer slots reject more requests; more slots answer more of them,
until whatever is behind the slots (here a sleep, in real life the model
provider's rate limit) becomes the bottleneck.
"""

from __future__ import annotations

import json
import math
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from load_service import AdmissionControl, Limits, TokenBucket, TokenBudget, fake_ask, secure, serve


# ------------------------------------------------------------------ the numbers
def percentile(values: list[float], p: float) -> float:
    """Nearest-rank percentile: the smallest value with at least p% of the values at or below it."""
    if not values:
        return float("nan")
    ordered = sorted(values)
    rank = max(1, math.ceil(p / 100 * len(ordered)))
    return ordered[rank - 1]


def summarize(results: list[tuple[int, float]], wall_seconds: float) -> dict:
    """results: (HTTP status, seconds) per request. Latency percentiles count answered (200) requests only."""
    answered = [seconds for status, seconds in results if status == 200]
    by_status: dict[int, int] = {}
    for status, _ in results:
        by_status[status] = by_status.get(status, 0) + 1
    return {
        "requests": len(results),
        "answered": len(answered),
        "throughput": round(len(answered) / wall_seconds, 2) if wall_seconds > 0 else 0.0,
        "p50": percentile(answered, 50),
        "p95": percentile(answered, 95),
        "p99": percentile(answered, 99),
        "by_status": dict(sorted(by_status.items())),
        "server_error_rate": sum(n for s, n in by_status.items() if s >= 500 or s == 0) / len(results) if results else 0.0,
    }


def slo_report(results: list[tuple[int, float]], latency_seconds: float, objective: float) -> dict:
    """A request is GOOD when it was answered within `latency_seconds`, or correctly refused with a 4xx.

    A 429 is the service doing its job (the user was over their limit); a 5xx or a slow answer is not.
    The error budget is the share of bad requests the objective allows: 1 - objective.
    """
    good = sum(1 for status, seconds in results
               if (status == 200 and seconds <= latency_seconds) or 400 <= status < 500)
    sli = good / len(results)
    budget = 1 - objective
    return {"sli": round(sli, 4), "objective": objective, "met": sli >= objective,
            "error_budget_used": round((1 - sli) / budget, 2) if budget else float("inf")}


# ------------------------------------------------------------------ the load (given)
def one_request(port: int, token: str) -> tuple[int, float]:
    request = urllib.request.Request(f"http://127.0.0.1:{port}/ask", data=b'{"question": "Is shipping free?"}',
                                     method="POST", headers={"Authorization": f"Bearer {token}"})
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        status = 0  # never reached the service: refused or reset by the operating system
    return status, time.perf_counter() - start


def run_load(max_concurrent: int, users: int = 16, per_user: int = 8, answer_seconds: float = 0.4,
             think_seconds: float = 0.1) -> dict:
    tokens = secure.TokenStore()
    user_tokens = [tokens.issue(f"user{i}", "customer") for i in range(users)]
    limits = Limits(rate=TokenBucket(per_minute=60, burst=5), budget=TokenBudget(per_day=1_000_000),
                    admission=AdmissionControl(max_concurrent=max_concurrent, max_queue=max_concurrent * 2,
                                               queue_timeout=1.5),
                    deadline=5)
    server = serve(0, fake_ask(answer_seconds), tokens, limits)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    def user_session(token: str) -> list[tuple[int, float]]:
        """A closed loop: one user sends a question, reads the answer, thinks briefly, asks again."""
        session = []
        for _ in range(per_user):
            session.append(one_request(port, token))
            time.sleep(think_seconds)
        return session

    start = time.perf_counter()
    try:
        with ThreadPoolExecutor(max_workers=users) as pool:
            results = [r for session in pool.map(user_session, user_tokens) for r in session]
    finally:
        server.shutdown()
        server.server_close()
    return {"summary": summarize(results, time.perf_counter() - start),
            "slo": slo_report(results, latency_seconds=2.0, objective=0.95)}


def main() -> None:
    for slots in (2, 8):
        report = run_load(slots)
        s, slo = report["summary"], report["slo"]
        print(f"\n{slots} concurrent slots: {s['requests']} requests, {s['answered']} answered, "
              f"{s['throughput']} answers/s")
        print(f"   latency  p50 {s['p50']:.2f} s   p95 {s['p95']:.2f} s   p99 {s['p99']:.2f} s")
        print(f"   status   {json.dumps(s['by_status'])}")
        print(f"   SLO      {slo['sli']:.1%} good (objective {slo['objective']:.0%}): "
              f"{'met' if slo['met'] else 'MISSED'}, error budget used x{slo['error_budget_used']}")
    print("\n429s are users over their rate limit (a burst of 5, then 1 per second): correct refusals, not failures.")


if __name__ == "__main__":
    main()
