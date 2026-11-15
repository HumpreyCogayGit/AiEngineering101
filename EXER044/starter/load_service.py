"""EXER044 — Operating Under Load (starter).

    uv run python EXER042/starter/secure_service.py issue ana customer
    set -a; source .env; set +a
    uv run python EXER044/starter/load_service.py                     # the helpdesk, with limits
    HELPDESK_FAKE_SECONDS=0.5 uv run python EXER044/starter/load_service.py   # a fake assistant, for experiments
    uv run python EXER044/starter/loadtest.py                         # a local load test and its report

The EXER042 service accepts every request, however many arrive, and lets each
one run for up to 300 seconds. Under load that ends in one of two ways: the
bill, or a service that answers nobody because it is trying to answer everybody.

A service under load needs to say NO early and clearly:

    413  the body is too large                        (before reading it)
    429  this user is over their rate or token budget  + Retry-After
    503  the service is full: no free slot, queue full + Retry-After
    504  the answer did not come within the deadline

and to stop cleanly: on SIGTERM it stops taking new work, finishes what it
started, and exits, instead of being killed mid-answer ten seconds later.
"""

from __future__ import annotations

import json
import logging
import math
import os
import signal
import sys
import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Mapping

from aicourse.stretch import solution_of

secure = solution_of("EXER042", "secure_service.py")  # authentication and namespaces (EXER042)
base = secure.base                                      # health and configuration (EXER041)
log = logging.getLogger("helpdesk")
MAX_BODY_BYTES = 20_000

Response = tuple[int, dict, dict[str, str]]


class Overloaded(Exception):
    """No slot and no room in the queue (or waited too long for one)."""


# ------------------------------------------------------------------ 1. rate limit per user
class TokenBucket:
    """`per_minute` requests per minute per user, with bursts of up to `burst`.

    Each user has a bucket of `burst` tokens that refills continuously. A request takes one.
    `clock` is injectable so the behaviour can be tested without waiting.
    """

    def __init__(self, per_minute: float, burst: int, clock: Callable[[], float] = time.monotonic) -> None:
        self.rate = per_minute / 60.0
        self.burst = burst
        self.clock = clock
        self.buckets: dict[str, tuple[float, float]] = {}  # user -> (tokens, last refill time)
        self.lock = threading.Lock()

    def take(self, user: str) -> float:
        """0.0 when the request may go ahead; otherwise the seconds until it may (for Retry-After).

        Under self.lock:
        - now = self.clock(); tokens, last = self.buckets.get(user, (float(self.burst), now))   # a new user starts full
        - refill: tokens = min(self.burst, tokens + (now - last) * self.rate)
        - tokens >= 1: store (tokens - 1, now) and return 0.0
        - otherwise:   store (tokens, now) and return the time until one whole token: (1 - tokens) / self.rate
        """
        # TODO
        raise NotImplementedError("take")


# ------------------------------------------------------------------ 2. token budget per user (given)
class TokenBudget:
    """Model tokens per user per UTC day. A rate limit counts requests; a budget counts cost."""

    def __init__(self, per_day: int, clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        self.per_day = per_day
        self.clock = clock
        self.spent: dict[tuple[str, str], int] = {}
        self.lock = threading.Lock()

    def _day(self) -> str:
        return self.clock().date().isoformat()

    def remaining(self, user: str) -> int:
        with self.lock:
            return self.per_day - self.spent.get((user, self._day()), 0)

    def spend(self, user: str, tokens: int) -> None:
        with self.lock:
            key = (user, self._day())
            self.spent[key] = self.spent.get(key, 0) + tokens

    def seconds_until_reset(self) -> int:
        now = self.clock()
        midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
        return max(1, int((midnight - now).total_seconds()))


# ------------------------------------------------------------------ 3. concurrency limit and bounded queue
class AdmissionControl:
    """At most `max_concurrent` questions run; at most `max_queue` wait, each for `queue_timeout` seconds."""

    def __init__(self, max_concurrent: int, max_queue: int, queue_timeout: float) -> None:
        self.slots = threading.Semaphore(max_concurrent)
        self.max_queue = max_queue
        self.queue_timeout = queue_timeout
        self.waiting = 0
        self.lock = threading.Lock()

    def acquire(self) -> None:
        """Take a slot, waiting in the queue if needed. Raise Overloaded instead of waiting forever.

        1. A free slot right now? self.slots.acquire(blocking=False) -> return.
        2. Under self.lock: if self.waiting >= self.max_queue, raise Overloaded("the queue is full");
           otherwise self.waiting += 1.
        3. Wait: self.slots.acquire(timeout=self.queue_timeout). False -> raise Overloaded(...).
        4. Whatever happens in step 3, decrement self.waiting again (try/finally, under the lock).
        """
        # TODO
        raise NotImplementedError("acquire")

    def release(self) -> None:
        self.slots.release()


# ------------------------------------------------------------------ 4. graceful shutdown
class GracefulShutdown:
    """Counts requests in flight (the HTTP handler calls start/end) and drains them on request."""

    def __init__(self) -> None:
        self.draining = False
        self.in_flight = 0
        self.cond = threading.Condition()

    def start(self) -> None:
        with self.cond:
            self.in_flight += 1

    def end(self) -> None:
        with self.cond:
            self.in_flight -= 1
            self.cond.notify_all()

    def drain(self, timeout: float) -> bool:
        """Stop taking new questions and wait for the running ones. True when all finished in time."""
        with self.cond:
            self.draining = True
            return self.cond.wait_for(lambda: self.in_flight == 0, timeout)


def install_sigterm_handler(server: ThreadingHTTPServer, shutdown: GracefulShutdown, grace: float) -> None:
    """On SIGTERM: drain, then stop the server. Register with signal.signal(signal.SIGTERM, handler).

    The handler runs on the MAIN thread, which is inside server.serve_forever(). server.shutdown()
    waits until serve_forever() returns, so calling it in the handler waits for itself forever.
    Instead, the handler starts a daemon thread that:
        1. shutdown.drain(grace)    new questions now get 503, readiness fails, running ones finish
        2. server.shutdown()        serve_forever() returns, main() closes the server and exits 0
    Log both steps. Process 1 in a container ignores SIGTERM unless a handler like this exists.
    """
    # TODO
    raise NotImplementedError("install_sigterm_handler")


# ------------------------------------------------------------------ 5. the routes
@dataclass
class Limits:
    rate: TokenBucket
    budget: TokenBudget
    admission: AdmissionControl
    deadline: float
    shutdown: GracefulShutdown = field(default_factory=GracefulShutdown)
    executor: ThreadPoolExecutor = field(default_factory=lambda: ThreadPoolExecutor(max_workers=32))


def default_limits() -> Limits:
    return Limits(rate=TokenBucket(per_minute=20, burst=5), budget=TokenBudget(per_day=200_000),
                  admission=AdmissionControl(max_concurrent=8, max_queue=16, queue_timeout=10), deadline=60)


def route(method: str, path: str, headers: Mapping[str, str], body: bytes, body_length: int,
          ask: Callable, tokens, limits: Limits) -> Response:
    """(status, JSON body, extra headers). Run the cheap checks first, so a rejection costs almost nothing.

    GET /healthz -> 200 {"status": "ok"}, also while draining (the process is alive)
    GET /readyz  -> 503 {"status": "draining"} while limits.shutdown.draining, else base.readiness()

    Then, in this order:
     1. body_length > MAX_BODY_BYTES                     -> 413   (the handler did not even read the body)
     2. principal = secure.authenticate(headers, tokens)  -> secure.UNAUTHORIZED when None   (EXER042)
     3. path != "/ask" -> 404;  method != "POST" -> 405
     4. limits.shutdown.draining                          -> 503, Retry-After "1"
     5. wait = limits.rate.take(user) > 0                 -> 429, Retry-After str(math.ceil(wait))
     6. limits.budget.remaining(user) <= 0                -> 429, Retry-After str(limits.budget.seconds_until_reset())
     7. parse the JSON as in EXER042 (question, thread_id, key = secure.thread_key(...)) -> 400 on problems
     8. limits.admission.acquire(); Overloaded            -> 503, Retry-After "2"
     9. future = limits.executor.submit(ask, question, key, principal)
        future.add_done_callback(lambda _: limits.admission.release())
           release when the work STOPS: a timed-out question keeps running and keeps its slot
    10. reply = future.result(timeout=limits.deadline); TimeoutError (concurrent.futures) -> 504;
        any other exception -> log.exception, 500
    11. limits.budget.spend(user, reply["tokens"]); return 200, {"thread_id": thread_id, **reply}, {}
    """
    # TODO
    raise NotImplementedError("route")


# ------------------------------------------------------------------ plumbing (given)
def make_handler(ask: Callable, tokens, limits: Limits) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _respond(self) -> None:
            limits.shutdown.start()  # counted until the response is WRITTEN, not just computed
            try:
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length <= MAX_BODY_BYTES else b""  # never read a huge body
                status, payload, extra = route(self.command, self.path.split("?")[0], dict(self.headers.items()),
                                               body, length, ask, tokens, limits)
                data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                for name, value in extra.items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(data)
            finally:
                limits.shutdown.end()

        do_GET = do_POST = _respond

        def log_message(self, fmt: str, *args) -> None:
            if self.path not in ("/healthz", "/readyz"):
                log.info("%s %s", self.address_string(), fmt % args)

    return Handler


class Server(ThreadingHTTPServer):
    # The kernel's accept queue is the FIRST queue in front of the service. socketserver's default
    # is 5: a burst of new connections beyond it is reset before any of our code runs.
    request_queue_size = 128


def serve(port: int, ask: Callable, tokens, limits: Limits) -> ThreadingHTTPServer:
    return Server(("0.0.0.0", port), make_handler(ask, tokens, limits))


def fake_ask(seconds: float) -> Callable:
    """An assistant that takes `seconds` and costs 1,200 tokens: for load tests and the shutdown check."""

    def ask(question: str, key: str, principal) -> dict:
        time.sleep(seconds)
        return {"answer": f"(fake) {question}", "tools_used": [], "blocked": False, "reasons": [], "tokens": 1200}

    return ask


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    fake = os.environ.get("HELPDESK_FAKE_SECONDS")
    try:
        port = base.service_port()
        if not fake:
            base.check_config()
    except base.ConfigError as exc:
        log.error("%s", exc)
        sys.exit(2)
    tokens = secure.load_tokens(Path(os.environ.get("HELPDESK_TOKENS_FILE", secure.TOKENS_FILE)))
    ask = fake_ask(float(fake)) if fake else secure.UserHelpdesks().ask
    limits = default_limits()
    server = serve(port, ask, tokens, limits)
    install_sigterm_handler(server, limits.shutdown, grace=float(os.environ.get("SHUTDOWN_GRACE_SECONDS", "25")))
    log.info("Nimbus Helpdesk (with limits) on port %d%s", port, " [fake assistant]" if fake else "")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    limits.executor.shutdown(wait=False, cancel_futures=True)
    log.info("stopped cleanly")


if __name__ == "__main__":
    main()
