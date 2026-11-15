"""EXER043 checks. Run:  uv run python EXER043/check.py

Everything runs offline: a fake payment gateway counts the money that really moved, and a
scripted model drives a real LangGraph agent through a crash and a resume.
"""

import threading

from langchain_core.messages import AIMessage

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model

checker = Checker(__file__)
mod = checker.load("refunds.py")


def fresh(supports_idempotency=True):
    return mod.Ledger(), mod.PaymentGateway(supports_idempotency)


@checker.check("idempotency_key(): the same decision gives the same key, another decision another key")
def _():
    a = mod.idempotency_key("thread-1", "call_7")
    assert a == mod.idempotency_key("thread-1", "call_7")
    assert a != mod.idempotency_key("thread-1", "call_8") and a != mod.idempotency_key("thread-2", "call_7")
    assert "thread-1" in a and "call_7" in a, "keep the parts readable: the key ends up in the audit log"


@checker.check("validate_refund() refuses unknown orders, non-positive amounts and over-refunds")
def _():
    assert mod.validate_refund("NC-1042", 3450, 0) is None
    assert mod.validate_refund("NC-1042", 1000, 2450) is None, "exactly what is left is allowed"
    for args in (("NC-9999", 10, 0), ("NC-1042", 0, 0), ("NC-1042", -5, 0), ("NC-1042", 3451, 0), ("NC-1042", 1001, 2450)):
        reason = mod.validate_refund(*args)
        assert isinstance(reason, str) and reason, f"{args} must be refused with a reason"


@checker.check("issue_refund() with the same key twice moves money once and returns the same answer")
def _():
    ledger, gateway = fresh()
    first = mod.issue_refund(ledger, gateway, "k1", "NC-1042", 3450, "test")
    second = mod.issue_refund(ledger, gateway, "k1", "NC-1042", 3450, "test")
    assert len(gateway.money_moved) == 1, gateway.money_moved
    assert first == second and gateway.money_moved[0]["refund_id"] in first, (first, second)
    assert [r["outcome"] for r in ledger.audit_rows()] == ["started", "executed", "replayed"], ledger.audit_rows()


@checker.check("a second decision for the same order cannot refund more than was paid")
def _():
    ledger, gateway = fresh()
    mod.issue_refund(ledger, gateway, "k1", "NC-1043", 600, "test")
    reply = mod.issue_refund(ledger, gateway, "k2", "NC-1043", 600, "test")
    assert reply.startswith("Refused") and len(gateway.money_moved) == 1, reply
    assert ledger.audit_rows()[-1]["outcome"] == "rejected"
    assert mod.issue_refund(ledger, gateway, "k3", "NC-1043", 240, "test").startswith("Refunded")


@checker.check("a crash after the money moved: the retry with the same key does not pay again")
def _():
    ledger, gateway = fresh()
    gateway.crash_after_next_refund = True
    try:
        mod.issue_refund(ledger, gateway, "k1", "NC-1042", 3450, "test")
    except mod.SimulatedCrash:
        pass
    else:
        raise AssertionError("the fake gateway should have crashed")
    assert ledger.get("k1")["status"] == "pending", "record the intent BEFORE calling the gateway"
    reply = mod.issue_refund(ledger, gateway, "k1", "NC-1042", 3450, "test")
    assert len(gateway.money_moved) == 1 and reply.startswith("Refunded"), (gateway.money_moved, reply)
    assert ledger.get("k1")["status"] == "done"
    assert [r["outcome"] for r in ledger.audit_rows()] == ["started", "started", "executed"], \
        "the audit shows both attempts, also the one that crashed"


@checker.check("without an idempotent gateway, an unknown outcome is flagged for a person, never retried")
def _():
    ledger, gateway = fresh(supports_idempotency=False)
    gateway.crash_after_next_refund = True
    try:
        mod.issue_refund(ledger, gateway, "k1", "NC-1042", 3450, "test")
    except mod.SimulatedCrash:
        pass
    reply = mod.issue_refund(ledger, gateway, "k1", "NC-1042", 3450, "test")
    assert len(gateway.money_moved) == 1 and gateway.calls == 1, "do not call a non-idempotent gateway again"
    assert ledger.get("k1")["status"] == "needs_review" and "flag" in reply.lower(), reply


@checker.check("eight concurrent requests with one key refund once")
def _():
    ledger, gateway = fresh()
    replies, errors = [], []

    def worker():
        try:
            replies.append(mod.issue_refund(ledger, gateway, "same", "NC-1044", 390, "test"))
        except BaseException as exc:  # report it from the main thread
            errors.append(exc)

    workers = [threading.Thread(target=worker) for _ in range(8)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    if errors:
        raise errors[0]
    assert len(gateway.money_moved) == 1, gateway.money_moved
    assert len(set(replies)) == 1, set(replies)


@checker.check("an agent that crashes in the refund tool and is resumed refunds once, with the same key")
def _():
    from langchain.agents import create_agent
    from langgraph.checkpoint.memory import InMemorySaver

    ledger, gateway = fresh()
    call = AIMessage(content="", tool_calls=[{"name": "refund_order", "args": {"order_id": "NC-1042", "amount": 3450},
                                              "id": "call_7"}])
    agent = create_agent(fake_chat_model(call, "Refunded."), [mod.make_refund_tool(ledger, gateway)],
                         checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "support-7"}}
    gateway.crash_after_next_refund = True
    try:
        agent.invoke({"messages": [("user", "refund NC-1042")]}, config)
    except mod.SimulatedCrash:
        pass
    assert agent.get_state(config).next == ("tools",), "the checkpoint should point at the tools node"
    agent.invoke(None, config)  # resume
    assert len(gateway.money_moved) == 1 and gateway.calls == 2, (gateway.money_moved, gateway.calls)
    keys = {row["key"] for row in ledger.audit_rows()}
    assert keys == {mod.idempotency_key("support-7", "call_7")}, keys
    assert all(row["actor"] and row["at"] for row in ledger.audit_rows())


checker.run()
