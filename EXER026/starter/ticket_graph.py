"""EXER026 — LangGraph Basics.

A graph = STATE (a typed dict shared by everyone) + NODES (functions that read
the state and return updates) + EDGES (what runs next; conditional edges
decide at runtime). No LLM is needed to learn the mechanics.

    uv run python EXER026/starter/ticket_graph.py
    uv run python EXER026/check.py
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class TicketState(TypedDict, total=False):
    ticket: str
    category: str
    priority: str
    response: str
    # TODO: add `steps`, a list[str] with a REDUCER so updates are APPENDED instead of replacing:
    #     steps: Annotated[list[str], operator.add]


KEYWORDS = {
    "billing": ["charge", "charged", "refund", "invoice", "payment", "card", "price", "receipt"],
    "technical": ["error", "crash", "bug", "broken", "slow", "not working", "login", "app"],
}
URGENT_WORDS = ["urgent", "asap", "immediately", "angry", "lawyer", "twice", "all my"]


# ------------------------------------------------------------------ nodes
# A node receives the whole state and returns ONLY the keys it changes.
def classify(state: TicketState) -> dict:
    """category = the first KEYWORDS entry with a word found in the lowercased ticket,
    else "general".  Return {"category": ..., "steps": ["classify"]}"""
    # TODO
    raise NotImplementedError("classify")


def prioritize(state: TicketState) -> dict:
    """priority = "high" if any URGENT_WORDS is in the lowercased ticket, else "normal".
    Return {"priority": ..., "steps": ["prioritize"]}"""
    # TODO
    raise NotImplementedError("prioritize")


def handle_billing(state: TicketState) -> dict:
    return {"response": "Our billing team will review your account within 24 hours.", "steps": ["billing"]}


def handle_technical(state: TicketState) -> dict:
    return {"response": "Please try updating the app; a technician will follow up.", "steps": ["technical"]}


def handle_general(state: TicketState) -> dict:
    return {"response": "Thanks for reaching out! We'll get back to you soon.", "steps": ["general"]}


def escalate(state: TicketState) -> dict:
    return {"response": state["response"] + " A supervisor has been notified.", "steps": ["escalate"]}


# ------------------------------------------------------------------ routers
# A router returns the NAME of the next node.
def route_by_category(state: TicketState) -> Literal["billing", "technical", "general"]:
    # TODO: return the category (it matches the node names)
    raise NotImplementedError("route_by_category")


def route_by_priority(state: TicketState) -> Literal["escalate", "__end__"]:
    # TODO: "escalate" for high priority, otherwise END
    raise NotImplementedError("route_by_priority")


# ------------------------------------------------------------------ graph
def build_graph():
    """Wire it up:

        START -> classify -> prioritize -(route_by_category)-> billing | technical | general
        each handler -(route_by_priority)-> escalate | END
        escalate -> END

    builder = StateGraph(TicketState)
    builder.add_node("classify", classify)   ... one per node ...
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("prioritize", route_by_category)
    return builder.compile()
    """
    # TODO
    raise NotImplementedError("build_graph")


def main() -> None:
    graph = build_graph()
    print("Graph as Mermaid (paste into https://mermaid.live):\n")
    print(graph.get_graph().draw_mermaid())
    for ticket in [
        "I was charged twice for my order, please refund ASAP!",
        "The app crashes when I open my cart.",
        "Do you have a store in Cebu?",
    ]:
        result = graph.invoke({"ticket": ticket})
        print(f"\n{ticket}\n  -> {result['category']}/{result['priority']}  steps={result['steps']}")
        print(f"  {result['response']}")

    print("\nStreaming the updates of each node:")
    for update in graph.stream({"ticket": "Urgent: login is broken"}, stream_mode="updates"):
        print("  ", update)


if __name__ == "__main__":
    main()
