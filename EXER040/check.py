"""EXER040 checks. Run:  uv run python EXER040/check.py

Everything is checked without Docker: the service functions are called directly, one real
HTTP round trip runs against a local port, and the Dockerfile is read as text. Building and
running the image is the manual part of the success criteria.
"""

import json
import os
import re
import threading
import urllib.error
import urllib.request

from aicourse.check import Checker
from aicourse.settings import ConfigError

checker = Checker(__file__)
mod = checker.load("service.py")
DOCKERFILE = checker.path("Dockerfile")
IGNORE = checker.path("Dockerfile.dockerignore")


def fake_ask(question, thread_id):
    return {"answer": f"echo: {question}", "tools_used": [], "blocked": False, "reasons": [], "tokens": 0}


def instructions(path):
    """The Dockerfile's instructions, comments removed and continuation lines joined."""
    text = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.strip().startswith("#"))
    return [re.sub(r"\s+", " ", line).strip() for line in text.replace("\\\n", " ").splitlines() if line.strip()]


@checker.check("service_port() reads PORT from the environment, defaults to 8000, rejects nonsense")
def _():
    assert mod.service_port({}) == 8000
    assert mod.service_port({"PORT": "9090"}) == 9090
    for bad in ("abc", "0", "70000", ""):
        try:
            mod.service_port({"PORT": bad})
        except ConfigError:
            continue
        raise AssertionError(f"PORT={bad!r} must raise ConfigError")


@checker.check("check_config() reads the environment only, and names what is missing")
def _():
    names = [k for k in os.environ if k.startswith(("AZURE_OPENAI_", "OLLAMA_", "AICOURSE_"))]
    saved = {k: os.environ.pop(k) for k in names}
    try:
        try:
            mod.check_config()  # default provider, nothing set: must fail even if a .env file exists
        except ConfigError as exc:
            assert "is missing" in str(exc), exc
        else:
            raise AssertionError("with an empty environment the configuration must be rejected: "
                                 "a deployed service must not read .env")
        os.environ["AICOURSE_PROVIDER"] = "ollama"  # a provider whose block has defaults for everything
        mod.check_config()
    finally:
        for k in ("AICOURSE_PROVIDER",):
            os.environ.pop(k, None)
        os.environ.update(saved)


@checker.check("liveness() is always 200 and depends on nothing")
def _():
    assert mod.liveness() == (200, {"status": "ok"})


@checker.check("readiness() is 200 when every check passes, and 503 with ALL the reasons otherwise")
def _():
    def broken():
        raise RuntimeError("index missing")

    def also_broken():
        raise ValueError("no key")

    status, body = mod.readiness({"a": lambda: None, "b": lambda: None})
    assert status == 200 and body == {"status": "ready", "checks": {"a": "ok", "b": "ok"}}, body
    status, body = mod.readiness({"a": broken, "b": lambda: None, "c": also_broken})
    assert status == 503 and body["status"] == "not ready", body
    assert "index missing" in body["checks"]["a"] and body["checks"]["b"] == "ok", body
    assert "no key" in body["checks"]["c"], "every check must run, also after one has failed"


@checker.check("route() serves /healthz, /readyz and POST /ask, and answers 400, 404 and 405 correctly")
def _():
    assert mod.route("GET", "/healthz", b"", fake_ask)[0] == 200
    assert mod.route("GET", "/readyz", b"", fake_ask)[0] in (200, 503)
    status, body = mod.route("POST", "/ask", json.dumps({"question": " Hi? ", "thread_id": "t1"}).encode(), fake_ask)
    assert status == 200 and body["answer"] == "echo: Hi?" and body["thread_id"] == "t1", body
    status, body = mod.route("POST", "/ask", b'{"question": "Hi"}', fake_ask)
    assert status == 200 and len(body["thread_id"]) >= 8, "a missing thread_id gets a new one"
    assert mod.route("POST", "/ask", b"not json", fake_ask)[0] == 400
    assert mod.route("POST", "/ask", b'{"q": "x"}', fake_ask)[0] == 400
    assert mod.route("POST", "/ask", b'{"question": "  "}', fake_ask)[0] == 400
    assert mod.route("GET", "/ask", b"", fake_ask)[0] == 405
    assert mod.route("GET", "/secret", b"", fake_ask)[0] == 404


@checker.check("a failing assistant gives a 500 that does not leak the error text")
def _():
    def exploding(question, thread_id):
        raise RuntimeError("api key sk-12345 rejected by https://internal.example")

    import logging
    logging.getLogger("helpdesk").setLevel(logging.CRITICAL)  # keep the expected traceback out of the output
    status, body = mod.route("POST", "/ask", b'{"question": "Hi"}', exploding)
    assert status == 500 and "error" in body, body
    assert "sk-12345" not in json.dumps(body) and "internal.example" not in json.dumps(body), body


@checker.check("the service answers real HTTP requests")
def _():
    server = mod.serve(0, fake_ask)  # port 0: the operating system picks a free one
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/healthz", timeout=5) as response:
            assert response.status == 200 and json.loads(response.read()) == {"status": "ok"}
            assert response.headers["Content-Type"].startswith("application/json")
        request = urllib.request.Request(f"http://127.0.0.1:{port}/ask", data=b'{"question": "ping"}', method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            assert json.loads(response.read())["answer"] == "echo: ping"
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/nope", timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("an unknown path must answer 404")
    finally:
        server.shutdown()
        server.server_close()


@checker.check("Dockerfile: locked dependencies, installed before the application code is copied")
def _():
    lines = instructions(DOCKERFILE)
    sync = [i for i, line in enumerate(lines) if line.startswith("RUN") and "uv sync" in line]
    assert sync, "install the dependencies with `uv sync`"
    assert "--frozen" in lines[sync[0]] or "--locked" in lines[sync[0]], "use --frozen: install exactly what uv.lock says"
    app_copy = [i for i, line in enumerate(lines) if line.startswith("COPY") and "service.py" in line]
    assert app_copy and sync[0] < app_copy[0], "run uv sync BEFORE copying the application, so the layer is cached"


@checker.check("Dockerfile: no secrets and no `COPY . .`")
def _():
    lines = instructions(DOCKERFILE)
    for line in lines:
        if line.startswith(("COPY", "ADD")):
            parts = line.split()[1:]
            assert "." not in parts[:-1] and "./" not in parts[:-1], f"copy only what the service needs, not everything: {line}"
            assert not any(re.fullmatch(r"\.?/?\.env", part) for part in parts), f"never copy .env into an image: {line}"
        if line.startswith(("ENV", "ARG")):
            assert not re.search(r"(API_KEY|SECRET|PASSWORD|TOKEN)\s*=?\s*\S", line, re.I), \
                f"no secrets in ENV or ARG, they stay in the image history: {line}"


@checker.check("Dockerfile: runs as a non-root user")
def _():
    users = [line.split()[1] for line in instructions(DOCKERFILE) if line.startswith("USER")]
    assert users, "add a USER instruction"
    assert users[-1] not in ("root", "0"), "the last USER must not be root"


@checker.check("Dockerfile: EXPOSE, a HEALTHCHECK on /healthz, and CMD in exec form")
def _():
    lines = instructions(DOCKERFILE)
    assert any(line.startswith("EXPOSE") for line in lines), "EXPOSE the port"
    health = [line for line in lines if line.startswith("HEALTHCHECK")]
    assert health and "/healthz" in health[0], "add a HEALTHCHECK that requests /healthz"
    commands = [line for line in lines if line.startswith("CMD")]
    assert commands, "add a CMD that starts the service"
    assert commands[-1].startswith("CMD [") and "service.py" in commands[-1], \
        'start the service in exec form: CMD ["python", ".../service.py"]'


@checker.check("Dockerfile.dockerignore keeps .env, .venv, .chroma and .git out of the build")
def _():
    patterns = {line.strip().rstrip("/") for line in IGNORE.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")}
    for needed in (".env", ".venv", ".chroma", ".git"):
        assert needed in patterns, f"{needed} is not ignored"


checker.run()
