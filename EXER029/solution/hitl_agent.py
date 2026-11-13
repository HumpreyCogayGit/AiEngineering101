"""EXER029 — Human in the Loop (reference solution).

Some actions must not happen without a human: sending email, refunds,
deleting data. `interrupt()` pauses the graph mid-node, saves everything with
the checkpointer, and returns control to your app. Later,
`Command(resume=decision)` continues exactly where it stopped.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from aicourse.llm import get_chat_model

OUTBOX: list[dict] = []     # emails "sent" by the agent
REFUNDS: list[dict] = []    # refunds "issued" by the agent

INBOX = [
    {"from": "carla@example.com", "subject": "Order #1042 arrived damaged",
     "body": "Hi, my Hand Grinder Pro (order #1042, ₱3,450) arrived with a cracked handle. Can you help?"},
    {"from": "dan@example.com", "subject": "Wholesale pricing",
     "body": "Hello, we run a small office (20 people). What are your wholesale terms?"},
]


@tool
def read_inbox() -> list[dict]:
    """Read the support inbox."""
    return INBOX


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email to a customer."""
    OUTBOX.append({"to": to, "subject": subject, "body": body})
    return f"Email sent to {to}."


@tool
def refund_order(order_id: str, amount: float) -> str:
    """Refund an order (amount in PHP)."""
    REFUNDS.append({"order_id": order_id, "amount": amount})
    return f"Refunded ₱{amount:.2f} for order {order_id}."


TOOLS = [read_inbox, send_email, refund_order]
RISKY = {"send_email", "refund_order"}
SYSTEM = ("You are a Nimbus Coffee support agent. Read the inbox and handle customer emails. "
          "Damaged items get a free replacement (see policy) — refund only if the customer asks. "
          "Sign emails as 'Nimbus Support'.")


def build_graph(llm: BaseChatModel, checkpointer=None):
    llm_with_tools = llm.bind_tools(TOOLS)

    def agent(state: MessagesState) -> dict:
        return {"messages": [llm_with_tools.invoke([SystemMessage(SYSTEM)] + state["messages"])]}

    def route(state: MessagesState) -> str:
        return "review" if state["messages"][-1].tool_calls else END

    def review(state: MessagesState) -> Command:
        last: AIMessage = state["messages"][-1]
        risky = [c for c in last.tool_calls if c["name"] in RISKY]
        if not risky:
            return Command(goto="tools")

        # Pause here. The value is shown to the human; the return value is their decision.
        decision = interrupt({
            "question": "Approve these actions?",
            "tool_calls": [{"id": c["id"], "name": c["name"], "args": c["args"]} for c in risky],
        })
        action = decision.get("action")

        if action == "approve":
            return Command(goto="tools")

        if action == "edit":
            edits = decision.get("args", {})  # {tool_call_id: new_args}
            new_calls = [{**c, "args": edits.get(c["id"], c["args"])} for c in last.tool_calls]
            # Same message id → the reducer REPLACES the original message instead of appending.
            edited = AIMessage(content=last.content, tool_calls=new_calls, id=last.id)
            return Command(goto="tools", update={"messages": [edited]})

        # reject: every requested call gets a ToolMessage so the conversation stays valid
        reason = decision.get("reason", "no reason given")
        rejections = [
            ToolMessage(content=f"Not executed: a human rejected this action ({reason}).", tool_call_id=c["id"])
            for c in last.tool_calls
        ]
        return Command(goto="agent", update={"messages": rejections})

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("review", review, destinations=("tools", "agent"))
    builder.add_node("tools", ToolNode(TOOLS, handle_tool_errors=True))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route, ["review", END])
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


def config_for(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def pending(result: dict) -> dict | None:
    """The interrupt payload if the graph is paused, else None."""
    interrupts = result.get("__interrupt__")
    return interrupts[0].value if interrupts else None


def start(graph, text: str, thread_id: str) -> dict:
    return graph.invoke({"messages": [("user", text)]}, config_for(thread_id))


def resume(graph, thread_id: str, decision: dict) -> dict:
    return graph.invoke(Command(resume=decision), config_for(thread_id))


def ask_human(payload: dict) -> dict:
    print("\n⏸  The agent wants to:")
    for call in payload["tool_calls"]:
        print(f"   [{call['id']}] {call['name']}({call['args']})")
    choice = input("approve / edit / reject? ").strip().lower()
    if choice.startswith("a"):
        return {"action": "approve"}
    if choice.startswith("e"):
        call = payload["tool_calls"][0]
        new_body = input("New email body / refund amount: ")
        key = "body" if "body" in call["args"] else "amount"
        value = float(new_body) if key == "amount" else new_body
        return {"action": "edit", "args": {call["id"]: {**call["args"], key: value}}}
    return {"action": "reject", "reason": input("Reason: ")}


def main() -> None:
    graph = build_graph(get_chat_model(temperature=0))
    result = start(graph, "Please handle the inbox.", "support-1")
    while (payload := pending(result)) is not None:
        result = resume(graph, "support-1", ask_human(payload))
    print("\nAgent:", result["messages"][-1].text)
    print("\nOutbox:", OUTBOX)
    print("Refunds:", REFUNDS)


if __name__ == "__main__":
    main()
