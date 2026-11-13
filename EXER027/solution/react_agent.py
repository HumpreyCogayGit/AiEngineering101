"""EXER027 — An Agent from Scratch (reference solution).

An agent is a loop: the model thinks → maybe calls tools → sees results →
thinks again → ... → answers. As a graph that is just TWO nodes and a
conditional edge. This is what create_agent (EXER017) builds for you.
"""

from __future__ import annotations

import ast
import operator
from datetime import datetime
from zoneinfo import ZoneInfo

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from aicourse.llm import get_chat_model

PRODUCTS = {
    "mount apo sunrise": {"price": 520, "roast": "light", "origin": "Davao"},
    "benguet highlands": {"price": 480, "roast": "medium", "origin": "Benguet"},
    "barako bold": {"price": 390, "roast": "dark", "origin": "Batangas"},
    "decaf cloud": {"price": 550, "roast": "medium", "origin": "Sagada"},
}
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg, ast.Pow: operator.pow}


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression such as '3 * (520 + 390)'."""
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("only arithmetic is allowed")
    return ev(ast.parse(expression, mode="eval").body)


@tool
def lookup_product(name: str) -> str:
    """Look up price (PHP per 250 g bag), roast and origin of a Nimbus coffee by name."""
    info = PRODUCTS.get(name.strip().lower())
    if not info:
        return f"Unknown product '{name}'. Known: {', '.join(p.title() for p in PRODUCTS)}"
    return f"{name.title()}: ₱{info['price']} per 250 g, {info['roast']} roast, from {info['origin']}"


@tool
def current_time(timezone: str = "Asia/Manila") -> str:
    """Current date and time in an IANA timezone, e.g. 'Asia/Manila' or 'Europe/London'."""
    return datetime.now(ZoneInfo(timezone)).strftime("%A %Y-%m-%d %H:%M")


TOOLS = [calculator, lookup_product, current_time]
SYSTEM = ("You are the Nimbus Coffee assistant. Use tools for prices and for ANY arithmetic. "
          "Think step by step and call tools as many times as needed.")


def should_continue(state: MessagesState) -> str:
    """The conditional edge: tools requested → run them; otherwise we're done."""
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END


def build_agent(llm: BaseChatModel, tools=TOOLS, system: str = SYSTEM):
    llm_with_tools = llm.bind_tools(tools)

    def agent(state: MessagesState) -> dict:
        response = llm_with_tools.invoke([SystemMessage(content=system)] + state["messages"])
        return {"messages": [response]}  # MessagesState's reducer APPENDS this

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))  # errors go back to the model
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", should_continue, ["tools", END])
    builder.add_edge("tools", "agent")   # ← the loop
    return builder.compile()


def run(graph, question: str, recursion_limit: int = 12) -> str:
    """Ask a question; stop runaway loops with the recursion limit."""
    try:
        result = graph.invoke({"messages": [("user", question)]}, {"recursion_limit": recursion_limit})
    except GraphRecursionError:
        return "Sorry — I couldn't finish that within my step limit."
    return result["messages"][-1].text


def main() -> None:
    graph = build_agent(get_chat_model(temperature=0))
    print(graph.get_graph().draw_mermaid())
    question = "I want 3 bags of Barako Bold and 2 of Mount Apo Sunrise. What's the total in pesos?"
    print(f"Q: {question}\n")
    for step in graph.stream({"messages": [("user", question)]}, stream_mode="updates"):
        for node, update in step.items():
            for m in update["messages"]:
                calls = [f"{c['name']}({c['args']})" for c in getattr(m, "tool_calls", [])]
                print(f"[{node}] {', '.join(calls) or m.text[:150]}")


if __name__ == "__main__":
    main()
