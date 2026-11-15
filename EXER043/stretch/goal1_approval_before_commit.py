"""EXER043 stretch goal 1 — a human approves large refunds, and the approval cannot pay twice (EXER029).

    uv run python EXER043/stretch/goal1_approval_before_commit.py      # offline: a scripted model

Refunds above ₱1,000 wait for a person. `interrupt()` inside the tool pauses the run;
`Command(resume=...)` continues it. What EXER029 did not show: on resume, the tool
function runs again FROM THE TOP. Every line before `interrupt()` executes twice.

So the order inside the tool is the whole design:
    1. read and validate          (safe to repeat)
    2. interrupt() for approval   (the run pauses here; on resume it returns the decision)
    3. issue_refund(key)          (the side effect, after the last interrupt, and idempotent anyway)

The counter below shows step 1 running twice and the money moving once.
"""

from __future__ import annotations

from typing import Annotated

from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

from aicourse.fakes import fake_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "refunds.py")
APPROVAL_ABOVE = 1000.0


def make_tool(ledger, gateway, runs: dict):
    @tool
    def refund_order(order_id: str, amount: float,
                     tool_call_id: Annotated[str, InjectedToolCallId], config: RunnableConfig) -> str:
        """Refund money for a Nimbus order. amount is in pesos."""
        runs["tool body"] += 1                      # 1. runs again on every resume
        thread_id = config["configurable"]["thread_id"]
        key = base.idempotency_key(thread_id, tool_call_id)
        reason = base.validate_refund(order_id, amount, ledger.refunded_total(order_id, excluding_key=key))
        if reason:
            return f"Refused: {reason}."
        if amount > APPROVAL_ABOVE:
            decision = interrupt({"order_id": order_id, "amount": amount, "key": key})   # 2.
            if not decision.get("approve"):
                ledger.audit(key, decision.get("by", "?"), order_id, amount, "declined", decision.get("note", ""))
                return "A supervisor declined this refund."
            actor = f"approved by {decision['by']}"
        else:
            actor = f"agent:{thread_id}"
        return base.issue_refund(ledger, gateway, key, order_id, amount, actor)   # 3.

    return refund_order


def main() -> None:
    ledger, gateway, runs = base.Ledger(), base.PaymentGateway(), {"tool body": 0}
    call = AIMessage(content="", tool_calls=[{"name": "refund_order",
                                              "args": {"order_id": "NC-1042", "amount": 3450}, "id": "call_1"}])
    agent = create_agent(fake_chat_model(call, "Your refund is approved and issued."),
                         [make_tool(ledger, gateway, runs)], checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "support-9"}}

    result = agent.invoke({"messages": [("user", "Refund my broken grinder, NC-1042.")]}, config)
    request = result["__interrupt__"][0].value
    print(f"paused: approve ₱{request['amount']:,.0f} for {request['order_id']}?  (tool body ran {runs['tool body']}x)")

    result = agent.invoke(Command(resume={"approve": True, "by": "supervisor:maya"}), config)
    print(f"resumed: {result['messages'][-1].text}   (tool body ran {runs['tool body']}x)")
    print(f"money moved {len(gateway.money_moved)} time(s)")
    for row in ledger.audit_rows():
        print(f"audit  {row['outcome']:<9} {row['actor']:<26} {row['key']}")
    assert len(gateway.money_moved) == 1 and runs["tool body"] == 2


if __name__ == "__main__":
    main()
