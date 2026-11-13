"""EXER029 checks (offline, fake model). Run:  uv run python EXER029/check.py"""

from langchain_core.messages import AIMessage, ToolMessage

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model

checker = Checker(__file__)
mod = checker.load("hitl_agent.py")

EMAIL = {"to": "carla@example.com", "subject": "Your order", "body": "We'll send a replacement."}


def wants(name, args, id="call_1"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": id}])


def fresh(*replies):
    mod.OUTBOX.clear()
    mod.REFUNDS.clear()
    return mod.build_graph(fake_chat_model(*replies))


@checker.check("safe tools run without asking (no interrupt)")
def _():
    graph = fresh(wants("read_inbox", {}), "You have 2 emails.")
    result = mod.start(graph, "check inbox", "t-safe")
    assert mod.pending(result) is None
    assert result["messages"][-1].text == "You have 2 emails."


@checker.check("a risky tool call pauses the graph BEFORE it runs")
def _():
    graph = fresh(wants("send_email", EMAIL), "Done.")
    result = mod.start(graph, "reply to carla", "t-pause")
    payload = mod.pending(result)
    assert payload and payload["tool_calls"][0]["name"] == "send_email", payload
    assert mod.OUTBOX == [], "the email was sent before approval!"


@checker.check("approve -> the action runs")
def _():
    graph = fresh(wants("send_email", EMAIL), "Email sent.")
    mod.start(graph, "reply", "t-approve")
    result = mod.resume(graph, "t-approve", {"action": "approve"})
    assert mod.pending(result) is None
    assert mod.OUTBOX == [EMAIL], mod.OUTBOX


@checker.check("edit -> the action runs with the human's arguments")
def _():
    graph = fresh(wants("refund_order", {"order_id": "1042", "amount": 9999.0}), "Refunded.")
    mod.start(graph, "refund", "t-edit")
    mod.resume(graph, "t-edit", {"action": "edit", "args": {"call_1": {"order_id": "1042", "amount": 3450.0}}})
    assert mod.REFUNDS == [{"order_id": "1042", "amount": 3450.0}], mod.REFUNDS


@checker.check("reject -> nothing runs and the agent is told why")
def _():
    graph = fresh(wants("refund_order", {"order_id": "1042", "amount": 3450.0}), "OK, I won't refund.")
    mod.start(graph, "refund", "t-reject")
    result = mod.resume(graph, "t-reject", {"action": "reject", "reason": "replace instead"})
    assert mod.REFUNDS == []
    tool_msgs = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert tool_msgs and "replace instead" in tool_msgs[-1].content, tool_msgs
    assert result["messages"][-1].text == "OK, I won't refund."


checker.run()
