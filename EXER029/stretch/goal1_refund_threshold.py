"""EXER029 stretch goal 1 — approval only for refunds above a threshold.

    uv run python EXER029/stretch/goal1_refund_threshold.py      # offline: a scripted model

"Is this tool risky?" becomes "is this CALL risky?". The decision looks at
the arguments: a ₱200 refund goes through, a ₱3,450 refund waits for a
person. Emails still always wait. The rule is a plain function of the tool
call, so it is easy to read, test and change.

The amount comes from the model. Read it defensively: an amount that is
missing or not a number is treated as risky.
"""

from __future__ import annotations

from typing import Callable

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from aicourse.fakes import fake_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "hitl_agent.py")

REFUND_LIMIT = 500.0  # PHP: refunds up to this amount need no approval


def needs_approval(call: dict) -> bool:
    if call["name"] == "refund_order":
        try:
            return float(call["args"].get("amount")) > REFUND_LIMIT
        except (TypeError, ValueError):
            return True  # cannot tell how much: ask
    return call["name"] in base.RISKY


def build_graph(llm, risky: Callable[[dict], bool] = needs_approval, checkpointer=None):
    """The exercise's graph, with the risk test passed in instead of a fixed set of tool names."""
    llm_with_tools = llm.bind_tools(base.TOOLS)

    def agent(state: MessagesState) -> dict:
        return {"messages": [llm_with_tools.invoke([SystemMessage(base.SYSTEM)] + state["messages"])]}

    def route(state: MessagesState) -> str:
        return "review" if state["messages"][-1].tool_calls else END

    def review(state: MessagesState) -> Command:
        last: AIMessage = state["messages"][-1]
        to_review = [c for c in last.tool_calls if risky(c)]
        if not to_review:
            return Command(goto="tools")
        decision = interrupt({
            "question": "Approve these actions?",
            "tool_calls": [{"id": c["id"], "name": c["name"], "args": c["args"]} for c in to_review],
        })
        if decision.get("action") == "approve":
            return Command(goto="tools")
        reason = decision.get("reason", "no reason given")
        return Command(goto="agent", update={"messages": [
            ToolMessage(content=f"Not executed: a human rejected this action ({reason}).", tool_call_id=c["id"])
            for c in last.tool_calls]})

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("review", review, destinations=("tools", "agent"))
    builder.add_node("tools", ToolNode(base.TOOLS, handle_tool_errors=True))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route, ["review", END])
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


def refund_call(order_id: str, amount: float) -> AIMessage:
    return AIMessage(content="", tool_calls=[
        {"name": "refund_order", "args": {"order_id": order_id, "amount": amount}, "id": f"call_{order_id}"}])


def main() -> None:
    for order_id, amount in (("1050", 200.0), ("1042", 3450.0)):
        base.REFUNDS.clear()
        graph = build_graph(fake_chat_model(refund_call(order_id, amount), "Done."))
        result = base.start(graph, f"Refund order {order_id}.", f"thread-{order_id}")
        payload = base.pending(result)
        print(f"\nRefund of ₱{amount:,.0f}: {'PAUSED for approval' if payload else 'ran without asking'}")
        if payload:
            print("  shown to the human:", payload["tool_calls"][0]["args"])
            print("  refunds so far:", base.REFUNDS)
            result = base.resume(graph, f"thread-{order_id}", {"action": "approve"})
        print("  refunds issued:", base.REFUNDS)


if __name__ == "__main__":
    main()
