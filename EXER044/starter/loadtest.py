"""EXER044 — a local load test and its report (starter).

    uv run python EXER044/starter/loadtest.py

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
    """Nearest-rank percentile: the smallest value with at least p% of the values at or below it.

    Empty list -> float("nan"). Sort; rank = max(1, math.ceil(p / 100 * n)); return ordered[rank - 1].
    (No interpolation: every reported latency is one a real request had.)
    """
    # TODO
    raise NotImplementedError("percentile")


def summarize(results: list[tuple[int, float]], wall_seconds: float) -> dict:
    """results: (HTTP status, seconds) per request. Return a dict with:

      requests           len(results)
      answered           how many have status 200
      throughput         answered / wall_seconds, rounded to 2 decimals
      p50, p95, p99      percentile() of the ANSWERED latencies only (a fast 503 is not a fast answer)
      by_status          {status: count}, sorted by status
      server_error_rate  share of requests with status >= 500 or 0 (0 = the connection never got through)
    """
    # TODO
    raise NotImplementedError("summarize")


def slo_report(results: list[tuple[int, float]], latency_seconds: float, objective: float) -> dict:
    """A request is GOOD when it was answered (200) within latency_seconds, or refused with a 4xx.
    A 429 is the service doing its job; a 5xx or a slow answer is not.

    Return {"sli": good / total rounded to 4 decimals, "objective": objective, "met": sli >= objective,
            "error_budget_used": (1 - sli) / (1 - objective), rounded to 2 decimals}
    error_budget_used 1.0 means the run used exactly the failures the objective allows.
    """
    # TODO
    raise NotImplementedError("slo_report")


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
