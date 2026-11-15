"""EXER042 — Identity and Tenant Boundaries (reference solution).

    uv run python EXER042/solution/secure_service.py issue ana customer     # prints a token, stores its hash
    uv run python EXER042/solution/secure_service.py issue ben staff
    set -a; source .env; set +a
    uv run python EXER042/solution/secure_service.py                        # the helpdesk on port 8000
    curl -X POST localhost:8000/ask -H "Authorization: Bearer <token>" -d '{"question": "Is shipping free?"}'

The EXER041 service answers anyone, and the CALLER chooses the thread_id. So
anyone who learns a thread id can read and continue someone else's
conversation. This lesson fixes the boundary in four places:

1. AUTHENTICATION  who is calling? A bearer token, looked up by its hash.
2. IDENTITY        the user comes from the token, never from the request body.
3. NAMESPACES      every thread and notes file belongs to one user: the user id
                   is part of the key, so another user's key cannot be built.
4. AUTHORIZATION   what may this user see? Staff documents are filtered out of
                   a customer's search at QUERY time, before the model sees them.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import secrets
import sys
import threading
import uuid
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Mapping, Protocol

from aicourse.stretch import solution_of

base = solution_of("EXER041", "service.py")  # liveness, readiness, configuration: unchanged
log = logging.getLogger("helpdesk")
HERE = Path(__file__).resolve().parent
TOKENS_FILE = HERE / "output" / "tokens.json"
NOTES_ROOT = HERE / "output" / "notes"

ROLES = {"customer", "staff"}
STAFF_ONLY_SOURCES = {"employee_handbook.pdf"}   # documents a customer must never retrieve
SAFE_ID = re.compile(r"[A-Za-z0-9_-]{1,64}")     # user ids and thread ids: no '/', no '..'


# ------------------------------------------------------------------ 1. authentication
@dataclass(frozen=True)
class Principal:
    """Who is calling, as established by the server. Never built from request JSON."""
    user_id: str
    role: str


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class TokenStore:
    """Bearer tokens stored as SHA-256 hashes, like passwords: a leaked file gives no usable token.

    Tokens are 32 random bytes, so a plain hash is enough (a slow password hash is for
    secrets people choose). Looking up the hash of the presented token also avoids comparing
    secrets character by character.
    """

    def __init__(self, records: Mapping[str, dict] | None = None) -> None:
        self._by_hash: dict[str, Principal] = {h: Principal(**r) for h, r in (records or {}).items()}

    def issue(self, user_id: str, role: str) -> str:
        if not SAFE_ID.fullmatch(user_id) or role not in ROLES:
            raise ValueError(f"bad user id or role: {user_id!r}, {role!r}")
        token = secrets.token_urlsafe(32)
        self._by_hash[token_hash(token)] = Principal(user_id, role)
        return token  # shown once; only the hash is kept

    def lookup(self, token: str) -> Principal | None:
        return self._by_hash.get(token_hash(token))

    def records(self) -> dict[str, dict]:
        return {h: {"user_id": p.user_id, "role": p.role} for h, p in self._by_hash.items()}


def bearer_token(headers: Mapping[str, str]) -> str | None:
    """The token from an `Authorization: Bearer <token>` header, or None."""
    value = next((v for k, v in headers.items() if k.lower() == "authorization"), "")
    scheme, _, token = value.strip().partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def authenticate(headers: Mapping[str, str], tokens: TokenStore) -> Principal | None:
    token = bearer_token(headers)
    return tokens.lookup(token) if token else None


# ------------------------------------------------------------------ 2 + 3. identity and namespaces
def thread_key(principal: Principal, thread_id: str) -> str:
    """The internal key of a conversation: the user id is part of it."""
    if not SAFE_ID.fullmatch(thread_id):
        raise ValueError("thread_id may contain only letters, digits, '-' and '_' (at most 64)")
    return f"{principal.user_id}/{thread_id}"


def notes_file(user_id: str, root: Path | None = None) -> Path:
    """One notes file per user, and a user id can never point outside `root`."""
    root = root or NOTES_ROOT
    if not SAFE_ID.fullmatch(user_id):
        raise ValueError(f"unsafe user id: {user_id!r}")
    path = (root / f"{user_id}.json").resolve()
    if path.parent != root.resolve():
        raise ValueError(f"unsafe user id: {user_id!r}")
    return path


# ------------------------------------------------------------------ 4. authorization of retrieval
def search_filter(principal: Principal) -> dict | None:
    """A Chroma `where` filter: what this principal may retrieve. None means everything."""
    if principal.role == "staff":
        return None
    return {"source": {"$nin": sorted(STAFF_ONLY_SOURCES)}}


def permitted_search(store, query: str, principal: Principal, k: int = 4) -> list:
    """Search only the documents this principal may read. The filter runs IN the query:
    removing documents after the model has seen them is too late."""
    return store.similarity_search(query, k=k, filter=search_filter(principal))


# ------------------------------------------------------------------ the routes
class Helpdesk(Protocol):
    def ask(self, question: str, key: str, principal: Principal) -> dict: ...
    def history(self, key: str) -> list[dict] | None: ...


Response = tuple[int, dict, dict[str, str]]
UNAUTHORIZED: Response = (401, {"error": "send a valid token: Authorization: Bearer <token>"},
                          {"WWW-Authenticate": 'Bearer realm="helpdesk"'})


def route(method: str, path: str, headers: Mapping[str, str], body: bytes,
          helpdesk: Helpdesk, tokens: TokenStore) -> Response:
    """(status, JSON body, extra headers) for one request."""
    if method == "GET" and path in ("/healthz", "/readyz"):  # the platform calls these without a token
        status, payload = base.liveness() if path == "/healthz" else base.readiness()
        return status, payload, {}

    principal = authenticate(headers, tokens)
    if principal is None:
        return UNAUTHORIZED

    if path == "/ask":
        if method != "POST":
            return 405, {"error": "use POST for /ask"}, {}
        try:
            data = json.loads(body or b"{}")
            question = data["question"]
        except (ValueError, KeyError, TypeError):
            return 400, {"error": 'send JSON like {"question": "...", "thread_id": "optional"}'}, {}
        if not isinstance(question, str) or not question.strip():
            return 400, {"error": "question must be a non-empty string"}, {}
        thread_id = str(data.get("thread_id") or uuid.uuid4().hex)  # any "user_id" in the body is ignored
        try:
            key = thread_key(principal, thread_id)
        except ValueError as exc:
            return 400, {"error": str(exc)}, {}
        try:
            reply = helpdesk.ask(question.strip(), key, principal)
        except Exception:
            log.exception("ask failed")
            return 500, {"error": "the assistant could not answer; try again later"}, {}
        return 200, {"thread_id": thread_id, **reply}, {}

    if path.startswith("/threads/"):
        if method != "GET":
            return 405, {"error": "use GET for /threads/<id>"}, {}
        thread_id = path.removeprefix("/threads/")
        try:
            messages = helpdesk.history(thread_key(principal, thread_id))
        except ValueError:
            messages = None
        if messages is None:  # 404 for "not yours" too: never confirm that someone else's thread exists
            return 404, {"error": "no such thread"}, {}
        return 200, {"thread_id": thread_id, "messages": messages}, {}

    return 404, {"error": f"no such route: {method} {path}"}, {}


# ------------------------------------------------------------------ plumbing (given)
class UserHelpdesks:
    """One EXER037 assistant per user: their own notes file, and a search tool with their filter.

    Every assistant runs on one shared event loop in a background thread (as in EXER041).
    """

    def __init__(self) -> None:
        import asyncio

        self.loop = asyncio.new_event_loop()
        self.assistants: dict[str, object] = {}
        self.lock = threading.Lock()
        threading.Thread(target=self.loop.run_forever, daemon=True).start()

    async def _assistant(self, principal: Principal):
        if principal.user_id not in self.assistants:
            from langchain_core.tools import tool

            from aicourse.rag import format_docs, get_vector_store

            sys.path.insert(0, str(base.capstone_dir()))
            import tools as capstone_tools
            from assistant import Assistant

            @tool
            def search_knowledge_base(query: str) -> str:
                """Search Nimbus Coffee's documents: products and prices, refunds, shipping, brewing,
                loyalty program, café locations and hours, careers and HR policies.
                Returns numbered passages with their source file names."""
                docs = permitted_search(get_vector_store(), query, principal)
                return format_docs(docs) if docs else "No matching documents."

            notes = await capstone_tools.load_mcp_tools(notes_file(principal.user_id))
            tools = [search_knowledge_base, capstone_tools.calculator, *notes]
            self.assistants[principal.user_id] = await Assistant(tools=tools).setup()
        return self.assistants[principal.user_id]

    async def _ask(self, question: str, key: str, principal: Principal) -> dict:
        from dataclasses import asdict

        assistant = await self._assistant(principal)
        return asdict(await assistant.ask(question, key))

    async def _history(self, key: str) -> list[dict] | None:
        user_id = key.split("/", 1)[0]
        assistant = self.assistants.get(user_id)
        if assistant is None:
            return None
        state = await assistant.agent.aget_state({"configurable": {"thread_id": key}})
        messages = state.values.get("messages", [])
        visible = [{"role": m.type, "text": m.text} for m in messages if m.type in ("human", "ai") and m.text]
        return visible or None

    def ask(self, question: str, key: str, principal: Principal) -> dict:
        import asyncio

        return asyncio.run_coroutine_threadsafe(self._ask(question, key, principal), self.loop).result(timeout=300)

    def history(self, key: str) -> list[dict] | None:
        import asyncio

        return asyncio.run_coroutine_threadsafe(self._history(key), self.loop).result(timeout=30)


def make_handler(helpdesk: Helpdesk, tokens: TokenStore) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _respond(self) -> None:
            length = min(int(self.headers.get("Content-Length") or 0), base.MAX_BODY_BYTES)
            status, payload, extra = route(self.command, self.path.split("?")[0], dict(self.headers.items()),
                                           self.rfile.read(length), helpdesk, tokens)
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            for name, value in extra.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)

        do_GET = do_POST = _respond

        def log_message(self, fmt: str, *args) -> None:
            if self.path != "/healthz":
                log.info("%s %s", self.address_string(), fmt % args)

    return Handler


def serve(port: int, helpdesk: Helpdesk, tokens: TokenStore) -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("0.0.0.0", port), make_handler(helpdesk, tokens))


def load_tokens(path: Path = TOKENS_FILE) -> TokenStore:
    return TokenStore(json.loads(path.read_text(encoding="utf-8")) if path.exists() else {})


def issue(user_id: str, role: str, path: Path = TOKENS_FILE) -> None:
    tokens = load_tokens(path)
    token = tokens.issue(user_id, role)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tokens.records(), indent=2), encoding="utf-8")
    print(f"Token for {user_id} ({role}), shown once:\n{token}")


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "issue":
        issue(sys.argv[2], sys.argv[3])
        return
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        port = base.service_port()
        base.check_config()
    except base.ConfigError as exc:
        log.error("%s", exc)
        sys.exit(2)
    tokens = load_tokens(Path(os.environ.get("HELPDESK_TOKENS_FILE", TOKENS_FILE)))
    server = serve(port, UserHelpdesks(), tokens)
    log.info("Nimbus Helpdesk (authenticated) on port %d", port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down")


if __name__ == "__main__":
    main()
