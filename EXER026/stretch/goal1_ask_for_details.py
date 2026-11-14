"""EXER026 stretch goal 1 — a node that asks for missing information, with a loop back.

    uv run python EXER026/stretch/goal1_ask_for_details.py            # scripted answers
    uv run python EXER026/stretch/goal1_ask_for_details.py --ask      # type the answers yourself

"Help" is not a ticket anyone can route. A new node asks the customer for
details, adds the answer to the ticket and sends the flow BACK to classify:
the first loop in the course's graphs.

    START -> check -> classify -> prioritize -> ...      (as before)
               |  ^
     too vague v  |
            ask_details        (at most MAX_QUESTIONS times: the limit is code, not hope)

The question is asked with a plain function, so the node can be tested.
EXER029 replaces it with interrupt(), which can wait for hours.
"""

from __future__ import annotations

import sys
from typing import Callable, Literal

from langgraph.graph import END, START, StateGraph

from aicourse.stretch import solution_module

base = solution_module(__file__, "ticket_graph.py")

MAX_QUESTIONS = 2
MIN_WORDS = 4


class State(base.TicketState, total=False):
    questions_asked: int


def check(state: State) -> dict:
    return {"steps": ["check"]}


def needs_details(state: State) -> Literal["ask_details", "classify"]:
    too_vague = len(state["ticket"].split()) < MIN_WORDS
    may_ask = state.get("questions_asked", 0) < MAX_QUESTIONS
    return "ask_details" if too_vague and may_ask else "classify"


def build_graph(ask: Callable[[str], str] = input):
    def ask_details(state: State) -> dict:
        reply = ask("Could you describe the problem in a sentence? ").strip()
        # `ticket` has no reducer, so this REPLACES it with the longer text.
        return {"ticket": f"{state['ticket']} {reply}".strip(),
                "questions_asked": state.get("questions_asked", 0) + 1,
                "steps": ["ask_details"]}

    builder = StateGraph(State)
    builder.add_node("check", check)
    builder.add_node("ask_details", ask_details)
    for name, node in [("classify", base.classify), ("prioritize", base.prioritize),
                       ("billing", base.handle_billing), ("technical", base.handle_technical),
                       ("general", base.handle_general), ("escalate", base.escalate)]:
        builder.add_node(name, node)
    builder.add_edge(START, "check")
    builder.add_conditional_edges("check", needs_details)
    builder.add_edge("ask_details", "check")          # <- the loop back
    builder.add_edge("classify", "prioritize")
    builder.add_conditional_edges("prioritize", base.route_by_category)
    for handler in ("billing", "technical", "general"):
        builder.add_conditional_edges(handler, base.route_by_priority)
    builder.add_edge("escalate", END)
    return builder.compile()


def main() -> None:
    interactive = "--ask" in sys.argv
    cases = [
        ("Help!", ["I was charged twice for my order, refund it asap"]),
        ("The app crashes when I open my cart.", []),
        ("hi", ["um", "..."]),  # never becomes clear: the loop must still end
    ]
    for ticket, answers in cases:
        replies = iter(answers)

        def scripted(prompt: str) -> str:
            reply = next(replies, "")
            print(f"    {prompt}{reply}")
            return reply

        graph = build_graph(input if interactive else scripted)
        print(f"\nTicket: {ticket!r}")
        result = graph.invoke({"ticket": ticket})
        print(f"  -> {result['category']}/{result['priority']}  steps={result['steps']}")
        print(f"  final ticket text: {result['ticket']!r}")


if __name__ == "__main__":
    main()
