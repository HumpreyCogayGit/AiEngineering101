"""EXER043 — Safe Side Effects (starter).

    uv run python EXER043/starter/refunds.py          # an agent issues a refund, crashes, resumes

A tool that CHANGES something (moves money, sends an email, saves a note) can
run more than once for one decision:

- the client times out and retries the request,
- a LangGraph run crashes in the tools node and is resumed from its checkpoint:
  the whole node runs again, with the same tool call,
- the process dies after the money moved but before the result was saved.

Tool calls are executed AT LEAST once. They become effectively once when every
execution of one decision carries the same IDEMPOTENCY KEY, and every system
that acts on it refuses to act twice for one key:

    the model DECIDES   AIMessage(tool_calls=[refund_order(NC-1042, 3450), id=call_7])  <- checkpointed
    the code COMMITS    key = thread + tool call id -> ledger row -> gateway(key) -> ledger done

An audit record for every attempt shows afterwards what happened, and why.
"""

from __future__ import annotations

import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolCallId, tool

DB_PATH = Path(__file__).resolve().parent / "output" / "refunds.sqlite"

ORDERS = {
    "NC-1042": {"customer": "carla", "paid": 3450.0, "item": "Hand Grinder Pro"},
    "NC-1043": {"customer": "dan", "paid": 840.0, "item": "2 x Benguet Highlands"},
    "NC-1044": {"customer": "ana", "paid": 390.0, "item": "Barako Bold"},
}


# ------------------------------------------------------------------ given: the outside world
class SimulatedCrash(BaseException):
    """The process dies. A BaseException, so no `except Exception` in the agent catches it."""


class PaymentGateway:
    """A fake payment provider. It records every refund that really moved money.

    supports_idempotency=True behaves like real payment APIs: a repeated key returns the
    first result and moves no money. crash_after_next_refund=True moves the money and then
    "kills the process" before the caller can record the result.
    """

    def __init__(self, supports_idempotency: bool = True) -> None:
        self.supports_idempotency = supports_idempotency
        self.money_moved: list[dict] = []
        self.calls = 0
        self.crash_after_next_refund = False
        self._by_key: dict[str, str] = {}
        self._lock = threading.Lock()

    def refund(self, order_id: str, amount: float, idempotency_key: str | None = None) -> str:
        with self._lock:
            self.calls += 1
            if self.supports_idempotency and idempotency_key in self._by_key:
                return self._by_key[idempotency_key]
            refund_id = f"re_{uuid.uuid4().hex[:10]}"
            self.money_moved.append({"refund_id": refund_id, "order_id": order_id, "amount": amount})
            if idempotency_key:
                self._by_key[idempotency_key] = refund_id
            if self.crash_after_next_refund:
                self.crash_after_next_refund = False
                raise SimulatedCrash("the process died after the money moved")
            return refund_id


class Ledger:
    """Our own record of every refund decision, keyed by idempotency key (SQLite, UNIQUE key)."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.db = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
        self.lock = threading.Lock()
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS refunds (key TEXT PRIMARY KEY, order_id TEXT, amount REAL,
                                                status TEXT, refund_id TEXT);
            CREATE TABLE IF NOT EXISTS audit (at TEXT, key TEXT, actor TEXT, order_id TEXT, amount REAL,
                                              outcome TEXT, detail TEXT);""")

    def get(self, key: str) -> dict | None:
        with self.lock:
            row = self.db.execute("SELECT key, order_id, amount, status, refund_id FROM refunds WHERE key = ?",
                                  (key,)).fetchone()
        return dict(zip(("key", "order_id", "amount", "status", "refund_id"), row)) if row else None

    def begin(self, key: str, order_id: str, amount: float) -> bool:
        """Record the intent as 'pending'. False when the key already has a row (atomic)."""
        with self.lock:
            cursor = self.db.execute("INSERT OR IGNORE INTO refunds VALUES (?, ?, ?, 'pending', NULL)",
                                     (key, order_id, amount))
        return cursor.rowcount == 1

    def complete(self, key: str, refund_id: str) -> None:
        with self.lock:
            self.db.execute("UPDATE refunds SET status = 'done', refund_id = ? WHERE key = ?", (refund_id, key))

    def mark(self, key: str, status: str) -> None:
        with self.lock:
            self.db.execute("UPDATE refunds SET status = ? WHERE key = ?", (status, key))

    def refunded_total(self, order_id: str, excluding_key: str | None = None) -> float:
        """Money refunded or in flight for an order (pending counts: it may have moved)."""
        with self.lock:
            row = self.db.execute("SELECT COALESCE(SUM(amount), 0) FROM refunds WHERE order_id = ? AND key != ?",
                                  (order_id, excluding_key or "")).fetchone()
        return float(row[0])

    def audit(self, key: str, actor: str, order_id: str, amount: float, outcome: str, detail: str = "") -> None:
        with self.lock:
            self.db.execute("INSERT INTO audit VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                             key, actor, order_id, amount, outcome, detail))

    def audit_rows(self) -> list[dict]:
        names = ("at", "key", "actor", "order_id", "amount", "outcome", "detail")
        with self.lock:
            return [dict(zip(names, r)) for r in self.db.execute("SELECT * FROM audit ORDER BY rowid")]


# ------------------------------------------------------------------ 1. the key
def idempotency_key(thread_id: str, tool_call_id: str) -> str:
    """One key per DECISION: f"refund:{thread_id}:{tool_call_id}".

    When LangGraph resumes a crashed run, the tools node runs again with the SAME tool call
    (same id) in the SAME thread, so this key is the same on every replay. A new decision by the
    model is a new tool call id, so it gets a new key.
    """
    # TODO
    raise NotImplementedError("idempotency_key")


# ------------------------------------------------------------------ 2. decide: may this refund happen?
def validate_refund(order_id: str, amount: float, already_refunded: float,
                    orders: dict = ORDERS) -> str | None:
    """None when the refund is allowed, otherwise a short reason (a str).

    - unknown order_id                          -> f"no order {order_id}"
    - amount <= 0                               -> "the amount must be positive"
    - amount > orders[order_id]["paid"] - already_refunded
                                                -> say how much is left to refund
    (Allow a refund of exactly what is left.)
    """
    # TODO
    raise NotImplementedError("validate_refund")


# ------------------------------------------------------------------ 3. commit, at most once per key
def issue_refund(ledger: Ledger, gateway: PaymentGateway, key: str, order_id: str, amount: float,
                 actor: str) -> str:
    """Refund `amount` for `order_id` at most once for `key`. Return a message for the model.

    1. existing = ledger.get(key). Status "done": audit "replayed" (detail: the refund id) and return
       the same message as the first time: f"Refunded ₱{amount:,.2f} for order {order_id} (refund {refund_id})."
    2. No row yet: reason = validate_refund(order_id, amount, ledger.refunded_total(order_id, excluding_key=key)).
       A reason -> audit "rejected" (detail: the reason) and return f"Refused: {reason}."
       Otherwise ledger.begin(key, order_id, amount): the intent is recorded BEFORE the money moves.
    3. A "pending" row (a previous attempt died) and NOT gateway.supports_idempotency: you cannot know
       whether the money moved. ledger.mark(key, "needs_review"), audit "needs_review", and return a
       message saying the refund was flagged for a person. Do NOT call the gateway.
    4. audit "started", then refund_id = gateway.refund(order_id, amount, idempotency_key=key),
       ledger.complete(key, refund_id), audit "executed" (detail: refund_id), return the message.

    Audit with ledger.audit(key, actor, order_id, amount, outcome, detail).
    """
    # TODO
    raise NotImplementedError("issue_refund")


# ------------------------------------------------------------------ 4. the tool the agent calls
def make_refund_tool(ledger: Ledger, gateway: PaymentGateway):
    """Return a @tool `refund_order(order_id: str, amount: float, tool_call_id, config) -> str`.

    - Give it a docstring the model can act on (what it does, the unit of amount).
    - Declare `tool_call_id: Annotated[str, InjectedToolCallId]` and `config: RunnableConfig`.
      LangChain fills both in; the model never sees them.
    - thread_id = config["configurable"]["thread_id"], key = idempotency_key(thread_id, tool_call_id)
    - return issue_refund(ledger, gateway, key, order_id, amount, actor=f"agent:{thread_id}")
    """
    # TODO
    raise NotImplementedError("make_refund_tool")


# ------------------------------------------------------------------ demo (given)
SYSTEM = ("You are Nimbus Coffee's support agent. Damaged items may be refunded in full. "
          "Use refund_order for refunds and report the refund id.")


def main() -> None:
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import InMemorySaver

    from aicourse.llm import get_chat_model

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    ledger, gateway = Ledger(DB_PATH), PaymentGateway()
    agent = create_agent(get_chat_model(temperature=0), [make_refund_tool(ledger, gateway)],
                         system_prompt=SYSTEM, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "support-7"}}
    gateway.crash_after_next_refund = True
    try:
        agent.invoke({"messages": [("user", "My Hand Grinder Pro (order NC-1042, I paid ₱3,450) arrived broken. Please refund it in full.")]},
                     config)
    except SimulatedCrash as exc:
        print(f"CRASH: {exc}. The checkpoint says the next step is {agent.get_state(config).next}.")
    result = agent.invoke(None, config)  # resume: the tools node runs again, with the same tool call
    print(f"\nagent: {result['messages'][-1].text}\n")
    print(f"Gateway: {gateway.calls} calls, money moved {len(gateway.money_moved)} time(s): {gateway.money_moved}")
    for row in ledger.audit_rows():
        print(f"audit  {row['at']}  {row['outcome']:<9} {row['order_id']} ₱{row['amount']:,.0f}  {row['key']}  {row['detail']}")


if __name__ == "__main__":
    main()
