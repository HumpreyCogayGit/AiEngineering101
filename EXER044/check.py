"""EXER044 checks. Run:  uv run python EXER044/check.py

Offline. The limits are tested with fake clocks and a fake assistant; the last check starts the
service as a real process, sends it SIGTERM in the middle of a question, and watches it drain.
"""

import json
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from aicourse.check import Checker

checker = Checker(__file__)
svc = checker.load("load_service.py")
lt = checker.load("loadtest.py")
secure = svc.secure


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def make_limits(slots=2, queue=1, queue_timeout=0.2, deadline=2.0, per_minute=60, burst=5, budget=100_000):
    return svc.Limits(rate=svc.TokenBucket(per_minute, burst), budget=svc.TokenBudget(budget),
                      admission=svc.AdmissionControl(slots, queue, queue_timeout), deadline=deadline)


def tokens_and_header(user="ana"):
    tokens = secure.TokenStore()
    return tokens, {"Authorization": f"Bearer {tokens.issue(user, 'customer')}"}


def ask_route(limits, ask, tokens, headers, body=b'{"question": "Is shipping free?"}'):
    return svc.route("POST", "/ask", headers, body, len(body), ask, tokens, limits)


@checker.check("percentile() uses the nearest rank; summarize() reports throughput, p50/p95/p99 and statuses")
def _():
    values = [float(v) for v in range(1, 101)]
    assert lt.percentile(values, 50) == 50 and lt.percentile(values, 95) == 95 and lt.percentile(values, 99) == 99
    assert lt.percentile([3.0, 1.0, 2.0], 50) == 2.0 and lt.percentile([7.0], 99) == 7.0
    results = [(200, 0.5)] * 8 + [(200, 2.0), (429, 0.01), (503, 0.01), (504, 5.0)]
    s = lt.summarize(results, wall_seconds=4.0)
    assert s["requests"] == 12 and s["answered"] == 9 and s["throughput"] == 2.25, s
    assert s["p50"] == 0.5 and s["p99"] == 2.0, "latency percentiles count answered requests only"
    assert s["by_status"] == {200: 9, 429: 1, 503: 1, 504: 1}, s["by_status"]
    assert abs(s["server_error_rate"] - 2 / 12) < 1e-9, s["server_error_rate"]


@checker.check("slo_report(): fast answers and 4xx refusals are good; slow answers and 5xx use the error budget")
def _():
    results = [(200, 0.5)] * 95 + [(429, 0.01)] * 3 + [(200, 9.0), (503, 0.01)]
    slo = lt.slo_report(results, latency_seconds=2.0, objective=0.95)
    assert slo["sli"] == 0.98 and slo["met"] and abs(slo["error_budget_used"] - 0.4) < 1e-9, slo
    bad = lt.slo_report([(200, 0.5)] * 9 + [(503, 0.0)], latency_seconds=2.0, objective=0.99)
    assert not bad["met"] and bad["error_budget_used"] == 10.0, bad


@checker.check("TokenBucket: a burst is allowed, then one request per refill, per user, with a Retry-After")
def _():
    clock = Clock()
    bucket = svc.TokenBucket(per_minute=60, burst=3, clock=clock)
    assert [bucket.take("ana") for _ in range(3)] == [0.0, 0.0, 0.0]
    wait = bucket.take("ana")
    assert 0.9 <= wait <= 1.0, f"one token per second: wait about 1 s, got {wait}"
    assert bucket.take("ben") == 0.0, "every user has their own bucket"
    clock.now += 1.0
    assert bucket.take("ana") == 0.0 and bucket.take("ana") > 0
    clock.now += 600
    assert [bucket.take("ana") for _ in range(4)][:3] == [0.0, 0.0, 0.0], "the bucket never holds more than the burst"


@checker.check("AdmissionControl: a full queue is refused at once; a queued request gives up after its timeout")
def _():
    admission = svc.AdmissionControl(max_concurrent=1, max_queue=1, queue_timeout=0.3)
    admission.acquire()  # the one slot is taken
    outcome = {}

    def queued():
        start = time.perf_counter()
        try:
            admission.acquire()
            outcome["result"] = "slot"
        except svc.Overloaded:
            outcome["result"] = "overloaded"
        outcome["seconds"] = time.perf_counter() - start

    waiter = threading.Thread(target=queued)
    waiter.start()
    time.sleep(0.05)
    start = time.perf_counter()
    try:
        admission.acquire()
    except svc.Overloaded:
        assert time.perf_counter() - start < 0.1, "a full queue must refuse immediately, not wait"
    else:
        raise AssertionError("the queue (1) is full: a third request must raise Overloaded")
    waiter.join()
    assert outcome["result"] == "overloaded" and 0.25 <= outcome["seconds"] < 1.0, outcome
    admission.release()
    admission.acquire()  # the slot is free again


@checker.check("route(): 413 before reading a huge body, 401 without a token, 429 with Retry-After over the rate")
def _():
    tokens, headers = tokens_and_header()
    limits = make_limits(burst=2)
    ask = svc.fake_ask(0)
    status, _, _ = svc.route("POST", "/ask", headers, b"", svc.MAX_BODY_BYTES + 1, ask, tokens, limits)
    assert status == 413, status
    assert ask_route(limits, ask, tokens, {})[0] == 401
    assert [ask_route(limits, ask, tokens, headers)[0] for _ in range(2)] == [200, 200]
    status, body, extra = ask_route(limits, ask, tokens, headers)
    assert status == 429 and int(extra["Retry-After"]) >= 1, (status, extra)


@checker.check("route(): the token budget is spent per answer, and an empty budget gives 429")
def _():
    tokens, headers = tokens_and_header()
    limits = make_limits(budget=2000)
    ask = svc.fake_ask(0)  # 1,200 tokens per answer
    assert ask_route(limits, ask, tokens, headers)[0] == 200
    assert limits.budget.remaining("ana") == 800
    assert ask_route(limits, ask, tokens, headers)[0] == 200
    status, body, extra = ask_route(limits, ask, tokens, headers)
    assert status == 429 and "budget" in body["error"] and int(extra["Retry-After"]) > 0, (status, body, extra)


@checker.check("route(): 503 with Retry-After when every slot and the queue are full; 504 after the deadline")
def _():
    tokens, headers = tokens_and_header()
    limits = make_limits(slots=1, queue=0, deadline=0.2, burst=10)
    slow = svc.fake_ask(0.6)
    first = {}
    t = threading.Thread(target=lambda: first.setdefault("r", ask_route(limits, slow, tokens, headers)))
    t.start()
    time.sleep(0.05)
    status, _, extra = ask_route(limits, slow, tokens, headers)
    assert status == 503 and "Retry-After" in extra, (status, extra)
    t.join()
    assert first["r"][0] == 504, f"the slow question must time out at the deadline: {first['r'][:2]}"
    time.sleep(0.5)  # the timed-out work finishes and frees its slot
    assert ask_route(limits, svc.fake_ask(0), tokens, headers)[0] == 200


@checker.check("draining: readiness and new questions answer 503, liveness stays 200")
def _():
    tokens, headers = tokens_and_header()
    limits = make_limits()
    assert limits.shutdown.drain(timeout=0.1)
    ask = svc.fake_ask(0)
    assert svc.route("GET", "/healthz", {}, b"", 0, ask, tokens, limits)[0] == 200
    assert svc.route("GET", "/readyz", {}, b"", 0, ask, tokens, limits)[0] == 503
    assert ask_route(limits, ask, tokens, headers)[0] == 503


@checker.check("the real process finishes a question in flight after SIGTERM, then exits 0")
def _():
    svc.route("GET", "/healthz", {}, b"", 0, None, None, make_limits())  # an unfinished route() reports TODO here
    with tempfile.TemporaryDirectory() as tmp:
        tokens = secure.TokenStore()
        token = tokens.issue("ana", "customer")
        (Path(tmp) / "tokens.json").write_text(json.dumps(tokens.records()))
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        env = {**os.environ, "PORT": str(port), "HELPDESK_FAKE_SECONDS": "1.5",
               "HELPDESK_TOKENS_FILE": str(Path(tmp) / "tokens.json"), "SHUTDOWN_GRACE_SECONDS": "10"}
        proc = subprocess.Popen([sys.executable, str(checker.path("load_service.py"))], env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            for _ in range(100):
                try:
                    urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1)
                    break
                except OSError:
                    time.sleep(0.1)
            result = {}

            def ask():
                request = urllib.request.Request(f"http://127.0.0.1:{port}/ask", data=b'{"question": "Hi"}',
                                                 method="POST", headers={"Authorization": f"Bearer {token}"})
                with urllib.request.urlopen(request, timeout=10) as response:
                    result["status"] = response.status

            client = threading.Thread(target=ask)
            client.start()
            time.sleep(0.4)
            sent = time.perf_counter()
            proc.send_signal(signal.SIGTERM)
            client.join(10)
            code = proc.wait(timeout=10)
            took = time.perf_counter() - sent
        finally:
            if proc.poll() is None:
                proc.kill()
        output = proc.stdout.read()
        assert result.get("status") == 200, f"the question in flight must be answered: {result}\n{output}"
        assert code == 0, f"exit code {code}: the process must stop by itself, not be killed\n{output}"
        assert took < 5, f"took {took:.1f} s: it should exit as soon as the request is done"


checker.run()
