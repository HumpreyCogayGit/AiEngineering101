"""EXER041 — Deploying the Capstone (starter).

    uv run python EXER041/starter/service.py              # the helpdesk as an HTTP service on port 8000
    curl localhost:8000/healthz
    curl localhost:8000/readyz
    curl -X POST localhost:8000/ask -d '{"question": "How long do I have to return unopened beans?"}'

A program on your laptop becomes a service when three things are true:

1. CONFIGURATION comes from the environment. No `.env` file is shipped: the
   platform that runs the container injects the variables.
2. It reports its own HEALTH, so the platform can restart it or hold traffic back:
       /healthz  liveness   "the process is running"            -> restart me if this fails
       /readyz   readiness  "I can serve a request right now"   -> send me no traffic if this fails
3. It runs the same way everywhere: a container image built from the lockfile.

The assistant itself is the one from EXER037, unchanged. This file is a thin
shell around `Assistant.ask`, exactly like cli.py and app.py were.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import threading
import uuid
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Mapping

from aicourse.settings import DATA_DIR, ConfigError, settings_from_environment

log = logging.getLogger("helpdesk")
ROOT = Path(__file__).resolve().parent.parent.parent
MAX_BODY_BYTES = 20_000


# ------------------------------------------------------------------ 1. configuration from the environment
def service_port(env: Mapping[str, str] = os.environ) -> int:
    """The port to listen on: the PORT variable (hosting platforms set it), default "8000".

    Read it from `env`, not from os.environ directly, so the function can be tested.
    Raise ConfigError when the value is not a number from 1 to 65535. Return an int.
    """
    # TODO
    raise NotImplementedError("service_port")


def capstone_dir(env: Mapping[str, str] = os.environ) -> Path:
    """Which EXER037 code to serve: HELPDESK_CODE=solution (default) or starter (your own)."""
    return ROOT / "EXER037" / env.get("HELPDESK_CODE", "solution")


# ------------------------------------------------------------------ 2. health
def check_config() -> None:
    """Raise if the configuration is not usable.

    One line: call settings_from_environment(). It reads real environment variables ONLY
    (no .env file) and raises ConfigError naming every missing variable.
    """
    # TODO
    raise NotImplementedError("check_config")


def check_knowledge_base() -> None:
    folder = DATA_DIR / "knowledge_base"
    if not folder.is_dir() or not any(folder.iterdir()):
        raise RuntimeError(f"no documents in {folder}")


READINESS_CHECKS: dict[str, Callable[[], None]] = {
    "config": check_config,
    "knowledge_base": check_knowledge_base,
}


def liveness() -> tuple[int, dict]:
    """Return (200, {"status": "ok"}). Always.

    Liveness answers one question: "is the process able to respond at all?". It must not call
    the model, the vector store or anything else: when a dependency has a bad minute, a failing
    liveness check makes the platform restart every container, which helps nobody.
    """
    # TODO
    raise NotImplementedError("liveness")


def readiness(checks: Mapping[str, Callable[[], None]] = READINESS_CHECKS) -> tuple[int, dict]:
    """Run every check in `checks` (name -> a function that raises when something is wrong).

    Return (200, {"status": "ready", "checks": {name: "ok", ...}}) when all pass, or
    (503, {"status": "not ready", "checks": {name: "ok" or the error text, ...}}) when any fails.
    Catch the exception of each check: a health endpoint reports problems, it never crashes.
    Run ALL checks even after one failed, so the response lists everything that is wrong.
    """
    # TODO
    raise NotImplementedError("readiness")


# ------------------------------------------------------------------ 3. the routes, as a plain function
def route(method: str, path: str, body: bytes, ask: Callable[[str, str], dict]) -> tuple[int, dict]:
    """Map one HTTP request to (status code, JSON body). No sockets here, so it is easy to test.

    `ask(question, thread_id)` returns the helpdesk's Reply as a dict.

    GET  /healthz  -> liveness()
    GET  /readyz   -> readiness()
    POST /ask      -> body is JSON {"question": "...", "thread_id": "optional"}
                      200, {"thread_id": ..., **ask(question, thread_id)}
                      400 when the body is not JSON, has no "question", or the question is empty
                      405 for any other method on /ask
                      500, {"error": "..."} when ask() raises: log the exception with log.exception(),
                           and do NOT put its text in the response (it may contain internal details)
                      a missing thread_id gets a new one: uuid.uuid4().hex
    anything else  -> 404
    """
    # TODO
    raise NotImplementedError("route")


# ------------------------------------------------------------------ plumbing (given)
class AssistantRunner:
    """Owns ONE event loop in a background thread and runs every `ask` on it.

    The HTTP server handles requests in threads, while the assistant (and its MCP tools)
    is async. One long-lived loop lets all requests share one assistant and its memory.
    """

    def __init__(self, code_dir: Path) -> None:
        self.code_dir = code_dir
        self.loop = asyncio.new_event_loop()
        self.assistant = None
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

    async def _ask(self, question: str, thread_id: str) -> dict:
        if self.assistant is None:  # created on the first question, then reused
            sys.path.insert(0, str(self.code_dir))
            from assistant import Assistant

            self.assistant = await Assistant().setup()
        return asdict(await self.assistant.ask(question, thread_id))

    def ask(self, question: str, thread_id: str) -> dict:
        return asyncio.run_coroutine_threadsafe(self._ask(question, thread_id), self.loop).result(timeout=300)


def make_handler(ask: Callable[[str, str], dict]) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _respond(self) -> None:
            length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
            status, payload = route(self.command, self.path.split("?")[0], self.rfile.read(length), ask)
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = _respond

        def log_message(self, fmt: str, *args) -> None:  # one log line per request, to stderr
            if self.path != "/healthz":  # the platform calls it every few seconds
                log.info("%s %s", self.address_string(), fmt % args)

    return Handler


def serve(port: int, ask: Callable[[str, str], dict]) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("0.0.0.0", port), make_handler(ask))  # 0.0.0.0: reachable from outside the container


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        port = service_port()
        check_config()  # fail fast: a container that cannot work should not start
    except ConfigError as exc:
        log.error("%s", exc)
        sys.exit(2)
    server = serve(port, AssistantRunner(capstone_dir()).ask)
    log.info("Nimbus Helpdesk listening on port %d (GET /healthz, GET /readyz, POST /ask)", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down")


if __name__ == "__main__":
    main()
