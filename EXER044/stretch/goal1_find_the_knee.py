"""EXER044 stretch goal 1 — find the concurrency limit where latency turns (the "knee").

    uv run python EXER044/stretch/goal1_find_the_knee.py      # offline: a simulated provider, about 1 minute

The right concurrency limit is not a guess. Behind the service is something with
a capacity of its own: the model provider's rate limit, or a GPU serving a local
model. Here it is simulated: the "provider" works on 4 requests at once and
queues the rest, which is what a rate-limited API looks like from outside.

The sweep runs the same closed-loop load with limits from 1 to 12 and reports
throughput and p95 for each. Throughput stops growing near the provider's
capacity; beyond it, extra slots only make every user wait longer inside the
service instead of getting a quick 503 they can retry. Pick the largest limit
whose p95 still meets the latency objective.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from aicourse.stretch import solution_path

solution_path(__file__)
import loadtest  # noqa: E402
import load_service as svc  # noqa: E402

PROVIDER_CAPACITY = 4
P95_OBJECTIVE = 1.5


def provider_ask(seconds: float = 0.3):
    capacity = threading.Semaphore(PROVIDER_CAPACITY)

    def ask(question, key, principal):
        with capacity:  # waiting here is invisible to the service: it just looks slow
            time.sleep(seconds)
        return {"answer": "...", "tools_used": [], "blocked": False, "reasons": [], "tokens": 1000}

    return ask


def run(limit: int, users: int = 16, per_user: int = 6) -> dict:
    tokens = svc.secure.TokenStore()
    user_tokens = [tokens.issue(f"u{i}", "customer") for i in range(users)]
    limits = svc.Limits(rate=svc.TokenBucket(per_minute=6000, burst=100), budget=svc.TokenBudget(10**9),
                        admission=svc.AdmissionControl(limit, max_queue=limit, queue_timeout=0.5), deadline=10)
    server = svc.serve(0, provider_ask(), tokens, limits)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    def session(token):
        out = []
        for _ in range(per_user):
            out.append(loadtest.one_request(port, token))
            time.sleep(0.05)
        return out

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=users) as pool:
        results = [r for s in pool.map(session, user_tokens) for r in s]
    wall = time.perf_counter() - start
    server.shutdown()
    server.server_close()
    return loadtest.summarize(results, wall)


def main() -> None:
    print(f"provider capacity: {PROVIDER_CAPACITY} at once; p95 objective {P95_OBJECTIVE} s\n")
    print(f"{'limit':>5} {'answers/s':>10} {'p95 s':>7} {'503s':>5}")
    best = None
    for limit in (1, 2, 4, 6, 8, 12):
        s = run(limit)
        print(f"{limit:>5} {s['throughput']:>10} {s['p95']:>7.2f} {s['by_status'].get(503, 0):>5}")
        if s["p95"] <= P95_OBJECTIVE:
            best = limit
    print(f"\nLargest limit that meets p95 <= {P95_OBJECTIVE} s: {best}. "
          f"Above {PROVIDER_CAPACITY}, throughput is flat: the provider is the bottleneck, not the service.")


if __name__ == "__main__":
    main()
