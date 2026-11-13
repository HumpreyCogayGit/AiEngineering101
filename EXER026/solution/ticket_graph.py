"""EXER026 — LangGraph Basics (reference solution).

A graph = STATE (a typed dict shared by everyone) + NODES (functions that read
the state and return updates) + EDGES (what runs next; conditional edges
decide at runtime). No LLM is needed to learn the mechanics.
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
    # A REDUCER: updates to `steps` are appended (operator.add) instead of replacing the list.
    steps: Annotated[list[str], operator.add]


KEYWORDS = {
    "billing": ["charge", "charged", "refund", "invoice", "payment", "card", "price", "receipt"],
    "technical": ["error", "crash", "bug", "broken", "slow", "not working", "login", "app"],
}
URGENT_WORDS = ["urgent", "asap", "immediately", "angry", "lawyer", "twice", "all my"]


# ------------------------------------------------------------------ nodes
def classify(state: TicketState) -> dict:
    text = state["ticket"].lower()
    category = "general"
    for name, words in KEYWORDS.items():
        if any(w in text for w in words):
            category = name
            break
    return {"category": category, "steps": ["classify"]}


def prioritize(state: TicketState) -> dict:
    text = state["ticket"].lower()
    priority = "high" if any(w in text for w in URGENT_WORDS) else "normal"
    return {"priority": priority, "steps": ["prioritize"]}


def handle_billing(state: TicketState) -> dict:
    return {"response": "Our billing team will review your account within 24 hours.", "steps": ["billing"]}


def handle_technical(state: TicketState) -> dict:
    return {"response": "Please try updating the app; a technician will follow up.", "steps": ["technical"]}


def handle_general(state: TicketState) -> dict:
    return {"response": "Thanks for reaching out! We'll get back to you soon.", "steps": ["general"]}


def escalate(state: TicketState) -> dict:
    return {"response": state["response"] + " A supervisor has been notified.", "steps": ["escalate"]}


# ------------------------------------------------------------------ routers
def route_by_category(state: TicketState) -> Literal["billing", "technical", "general"]:
    return state["category"]


def route_by_priority(state: TicketState) -> Literal["escalate", "__end__"]:
    return "escalate" if state["priority"] == "high" else END


# ------------------------------------------------------------------ graph
def build_graph():
    builder = StateGraph(TicketState)
    builder.add_node("classify", classify)
    builder.add_node("prioritize", prioritize)
    builder.add_node("billing", handle_billing)
    builder.add_node("technical", handle_technical)
    builder.add_node("general", handle_general)
    builder.add_node("escalate", escalate)

    builder.add_edge(START, "classify")
    builder.add_edge("classify", "prioritize")
    builder.add_conditional_edges("prioritize", route_by_category)
    for handler in ("billing", "technical", "general"):
        builder.add_conditional_edges(handler, route_by_priority)
    builder.add_edge("escalate", END)
    return builder.compile()


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
