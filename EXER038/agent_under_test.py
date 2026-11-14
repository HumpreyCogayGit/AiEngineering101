"""The agent that EXER038 evaluates (given: you don't need to change it).

A small Nimbus Coffee order assistant with three tools. It is the kind of
agent you built in EXER027; here it is the SUBJECT of the exercise, not the
exercise. Your job is to score what it does.
"""

from __future__ import annotations

import ast
import operator

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool

PRODUCTS = {
    "mount apo sunrise": {"price": 520, "roast": "light"},
    "benguet highlands": {"price": 480, "roast": "medium"},
    "barako bold": {"price": 390, "roast": "dark"},
    "decaf cloud": {"price": 550, "roast": "medium"},
}
HOURS = {"makati": "6:30–21:00 daily", "bgc": "7:00–22:00 daily", "quezon city": "7:00–20:00, closed Mondays"}
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg}


def evaluate_expression(expression: str) -> float:
    """Arithmetic only (+ - * / and numbers). Raises ValueError for anything else."""
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("only arithmetic is allowed")
    try:
        return ev(ast.parse(expression, mode="eval").body)
    except SyntaxError as exc:
        raise ValueError(f"not an arithmetic expression: {expression!r}") from exc


@tool
def lookup_product(name: str) -> str:
    """Price (PHP per 250 g bag) and roast of ONE Nimbus coffee, by its name."""
    info = PRODUCTS.get(name.strip().lower())
    if not info:
        return f"Unknown product '{name}'. Known: {', '.join(p.title() for p in PRODUCTS)}"
    return f"{name.title()}: ₱{info['price']} per 250 g bag, {info['roast']} roast"


@tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic expression such as '3 * 390 + 2 * 520'. Use it for ANY arithmetic."""
    try:
        result = evaluate_expression(expression)
    except (ValueError, ZeroDivisionError) as exc:
        return f"Error: {exc}"
    return str(int(result)) if float(result).is_integer() else str(round(result, 4))


@tool
def store_hours(branch: str) -> str:
    """Opening hours of a Nimbus café branch: Makati, BGC or Quezon City."""
    return HOURS.get(branch.strip().lower(), f"No branch called {branch}. Branches: Makati, BGC, Quezon City.")


TOOLS = [lookup_product, calculator, store_hours]
SYSTEM = ("You are the Nimbus Coffee order assistant. Use lookup_product for every price, "
          "calculator for every calculation and store_hours for opening hours. "
          "Call a tool only when the question needs it. Answer in one or two sentences.")


def build_agent(llm: BaseChatModel, system: str = SYSTEM):
    return create_agent(llm, TOOLS, system_prompt=system)
