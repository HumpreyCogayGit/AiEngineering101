"""EXER044 stretch goal 2 — a client that honours Retry-After, against one that does not (EXER011).

    uv run python EXER044/stretch/goal2_retry_after_client.py      # offline: a fake assistant, about 20 s

EXER011 built the client side of reliability: retry temporary errors with
exponential backoff and jitter. This lesson built the server side: 429 and 503
come with Retry-After. They only help each other if the client listens.

Two kinds of client send the same 60 questions to the same busy service:

- impatient: retries every 429/503 at once, up to 20 times
- polite:    waits Retry-After (or EXER011's backoff when there is none), plus jitter

The impatient clients send many more requests and still get fewer answers. Under
real load those extra requests are what keeps the service overloaded: a retry storm.
"""

from __future__ import annotations

import random
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from aicourse.stretch import solution_module, solution_path

solution_path(__file__)
import load_service as svc  # noqa: E402

reliable = solution_module(__file__, "reliable.py", exercise="EXER011")


def send(port: int, token: str) -> tuple[int, float | None]:
    request = urllib.request.Request(f"http://127.0.0.1:{port}/ask", data=b'{"question": "Hi"}', method="POST",
                                     headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            return response.status, None
    except urllib.error.HTTPError as exc:
        retry_after = exc.headers.get("Retry-After")
        return exc.code, float(retry_after) if retry_after else None


def ask_until_answered(port: int, token: str, polite: bool, counter: list) -> bool:
    for attempt in range(1, 21):
        status, retry_after = send(port, token)
        counter.append(status)
        if status == 200:
            return True
        if status not in (429, 503):
            return False
        if polite:
            wait = retry_after if retry_after is not None else reliable.backoff_delay(attempt, 0.2)
            time.sleep(wait * random.uniform(1.0, 1.5))  # jitter: do not all come back at the same instant
    return False


def run(polite: bool, users: int = 12, questions: int = 5) -> None:
    tokens = svc.secure.TokenStore()
    user_tokens = [tokens.issue(f"u{i}", "customer") for i in range(users)]
    limits = svc.Limits(rate=svc.TokenBucket(per_minute=60, burst=3), budget=svc.TokenBudget(10**9),
                        admission=svc.AdmissionControl(3, max_queue=3, queue_timeout=0.3), deadline=10)
    server = svc.serve(0, svc.fake_ask(0.3), tokens, limits)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    sent: list[int] = []
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=users) as pool:
        answered = sum(pool.map(lambda t: sum(ask_until_answered(port, t, polite, sent) for _ in range(questions)),
                                user_tokens))
    took = time.perf_counter() - start
    server.shutdown()
    server.server_close()
    label = "polite   " if polite else "impatient"
    print(f"{label} answered {answered}/{users * questions} in {took:4.1f} s, sending {len(sent)} requests "
          f"({len(sent) / answered:.1f} per answer): 429={sent.count(429)} 503={sent.count(503)}")


def main() -> None:
    run(polite=False)
    run(polite=True)
    print("\nThe impatient clients burn their 20 retries inside one rate-limit window and give up; the polite ones "
          "wait as told and get every answer, with a fraction of the requests. Every refused request still costs "
          "the service a connection, a parse and a rate-limit check.")


if __name__ == "__main__":
    main()
