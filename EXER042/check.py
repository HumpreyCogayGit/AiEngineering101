"""EXER042 checks. Run:  uv run python EXER042/check.py

The routes are called directly with a fake helpdesk that records what it was asked,
plus one real HTTP round trip. The last check searches the real vector index.
"""

import json
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("secure_service.py")


class FakeHelpdesk:
    """Remembers conversations by key, exactly as the real one does."""

    def __init__(self):
        self.calls = []
        self.threads = {}

    def ask(self, question, key, principal):
        self.calls.append((question, key, principal))
        self.threads.setdefault(key, []).append({"role": "human", "text": question})
        return {"answer": f"echo: {question}", "tools_used": [], "blocked": False, "reasons": [], "tokens": 0}

    def history(self, key):
        return self.threads.get(key)


def setup():
    tokens = mod.TokenStore()
    ana = tokens.issue("ana", "customer")
    ben = tokens.issue("ben", "staff")
    return tokens, {"Authorization": f"Bearer {ana}"}, {"Authorization": f"Bearer {ben}"}


def ask(helpdesk, tokens, headers, payload):
    return mod.route("POST", "/ask", headers, json.dumps(payload).encode(), helpdesk, tokens)


@checker.check("bearer_token() reads 'Authorization: Bearer <token>' and nothing else")
def _():
    assert mod.bearer_token({"Authorization": "Bearer abc123"}) == "abc123"
    assert mod.bearer_token({"authorization": "bearer abc123 "}) == "abc123", "header names and the scheme are case-insensitive"
    for headers in ({}, {"Authorization": "Basic abc123"}, {"Authorization": "Bearer "}, {"Authorization": "abc123"}):
        assert mod.bearer_token(headers) is None, headers


@checker.check("authenticate() returns the principal of a valid token, None otherwise; only hashes are stored")
def _():
    tokens = mod.TokenStore()
    token = tokens.issue("ana", "customer")
    assert mod.authenticate({"Authorization": f"Bearer {token}"}, tokens) == mod.Principal("ana", "customer")
    assert mod.authenticate({"Authorization": f"Bearer {token}x"}, tokens) is None
    assert mod.authenticate({}, tokens) is None
    assert token not in json.dumps(tokens.records()), "never store the token itself"


@checker.check("health routes need no token; every other route answers 401 with WWW-Authenticate without one")
def _():
    tokens, _, _ = setup()
    helpdesk = FakeHelpdesk()
    assert mod.route("GET", "/healthz", {}, b"", helpdesk, tokens)[0] == 200
    assert mod.route("GET", "/readyz", {}, b"", helpdesk, tokens)[0] in (200, 503)
    for headers in ({}, {"Authorization": "Bearer not-a-token"}):
        status, body, extra = ask(helpdesk, tokens, headers, {"question": "Hi"})
        assert status == 401 and extra.get("WWW-Authenticate", "").startswith("Bearer"), (status, extra)
    status, _, _ = mod.route("GET", "/threads/t1", {}, b"", helpdesk, tokens)
    assert status == 401
    assert not helpdesk.calls, "an unauthenticated request must never reach the assistant"


@checker.check("the user comes from the token: a user_id in the request body changes nothing")
def _():
    tokens, ana, _ = setup()
    helpdesk = FakeHelpdesk()
    status, body, _ = ask(helpdesk, tokens, ana, {"question": "Hi", "thread_id": "t1", "user_id": "ben"})
    assert status == 200 and body["thread_id"] == "t1", body
    _, key, principal = helpdesk.calls[0]
    assert principal == mod.Principal("ana", "customer"), principal
    assert key == "ana/t1", key


@checker.check("user B can neither read nor continue user A's thread")
def _():
    tokens, ana, ben = setup()
    helpdesk = FakeHelpdesk()
    ask(helpdesk, tokens, ana, {"question": "My order number is NC-4471", "thread_id": "t1"})
    status, body, _ = mod.route("GET", "/threads/t1", ana, b"", helpdesk, tokens)
    assert status == 200 and "NC-4471" in json.dumps(body), body
    status, body, _ = mod.route("GET", "/threads/t1", ben, b"", helpdesk, tokens)
    assert status == 404 and "NC-4471" not in json.dumps(body), (status, body)
    ask(helpdesk, tokens, ben, {"question": "What was my order number?", "thread_id": "t1"})
    assert helpdesk.calls[-1][1] != "ana/t1", "B's question must go to B's own conversation"


@checker.check("thread ids and user ids cannot escape their namespace")
def _():
    tokens, ana, _ = setup()
    helpdesk = FakeHelpdesk()
    for bad in ("../ben/t1", "ben/t1", "a" * 65):
        status, _, _ = ask(helpdesk, tokens, ana, {"question": "Hi", "thread_id": bad})
        assert status == 400, f"thread_id {bad!r} must be rejected"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert mod.notes_file("ana", root) == (root / "ana.json").resolve()
        assert mod.notes_file("ana", root) != mod.notes_file("ben", root)
        for bad in ("../ana", "ana/../../x", "", "a b"):
            try:
                mod.notes_file(bad, root)
            except ValueError:
                continue
            raise AssertionError(f"notes_file({bad!r}) must raise ValueError")


@checker.check("search_filter(): customers cannot retrieve staff-only documents, staff can retrieve everything")
def _():
    customer, staff = mod.Principal("ana", "customer"), mod.Principal("ben", "staff")
    assert mod.search_filter(staff) is None
    where = mod.search_filter(customer)
    assert where == {"source": {"$nin": ["employee_handbook.pdf"]}}, where

    class Store:
        def similarity_search(self, query, k, filter=None):
            self.seen = (query, k, filter)
            return []

    store = Store()
    mod.permitted_search(store, "vacation days", customer)
    assert store.seen == ("vacation days", 4, where), "the filter must be part of the query itself"


@checker.check("the service answers real HTTP requests, with the token in a header")
def _():
    tokens, ana, _ = setup()
    mod.route("GET", "/healthz", {}, b"", FakeHelpdesk(), tokens)  # an unfinished route() reports TODO here
    server = mod.serve(0, FakeHelpdesk(), tokens)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{port}/ask"
        try:
            urllib.request.urlopen(urllib.request.Request(url, data=b'{"question": "Hi"}', method="POST"), timeout=5)
        except urllib.error.HTTPError as exc:
            assert exc.code == 401 and exc.headers["WWW-Authenticate"].startswith("Bearer")
        else:
            raise AssertionError("no token must give 401")
        request = urllib.request.Request(url, data=b'{"question": "Hi"}', method="POST", headers=ana)
        with urllib.request.urlopen(request, timeout=5) as response:
            assert json.loads(response.read())["answer"] == "echo: Hi"
    finally:
        server.shutdown()
        server.server_close()


@checker.check("a customer's search of the real index never returns the staff handbook  [live API]")
def _():
    from aicourse.rag import get_vector_store

    store = get_vector_store()
    question = "How many days of paid vacation leave do full-time employees get?"
    staff = {d.metadata["source"] for d in mod.permitted_search(store, question, mod.Principal("ben", "staff"))}
    customer = {d.metadata["source"] for d in mod.permitted_search(store, question, mod.Principal("ana", "customer"))}
    assert "employee_handbook.pdf" in staff, f"staff should find the handbook: {staff}"
    assert "employee_handbook.pdf" not in customer, f"customers must not: {customer}"


checker.run()
