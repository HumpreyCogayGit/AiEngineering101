"""Helpdesk tools: knowledge base search (RAG), a calculator, and MCP notes tools."""

from __future__ import annotations

import ast
import operator
import os
import sys
from pathlib import Path

from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient

from aicourse.rag import format_docs, get_vector_store

SERVERS = Path(__file__).resolve().parent.parent / "servers"
DEFAULT_NOTES = Path(__file__).resolve().parent / "output" / "notes.json"
ALLOWED_MCP_TOOLS = {"notes_add_note", "notes_list_notes", "notes_search_notes"}

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.USub: operator.neg}


@tool
def search_knowledge_base(query: str) -> str:
    """Search Nimbus Coffee's documents: products and prices, refunds, shipping, brewing,
    loyalty program, café locations and hours, careers and HR policies.
    Returns numbered passages with their source file names."""
    docs = get_vector_store().similarity_search(query, k=4)
    return format_docs(docs) if docs else "No matching documents."


@tool
def calculator(expression: str) -> str:
    """Evaluate arithmetic exactly, e.g. '3 * 390 + 250'. Use it for every calculation."""
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError("only + - * / and numbers are allowed")
    try:
        result = ev(ast.parse(expression, mode="eval").body)
    except Exception as exc:  # return errors to the model instead of crashing the agent
        return f"Error: {exc}"
    return str(int(result)) if float(result).is_integer() else str(round(result, 4))


LOCAL_TOOLS = [search_knowledge_base, calculator]


async def load_mcp_tools(notes_file: str | Path = DEFAULT_NOTES):
    client = MultiServerMCPClient({
        "notes": {
            "command": sys.executable,
            "args": [str(SERVERS / "notes_server.py")],
            "transport": "stdio",
            "env": {**os.environ, "NOTES_FILE": str(notes_file)},
        }
    }, tool_name_prefix=True)
    return [t for t in await client.get_tools() if t.name in ALLOWED_MCP_TOOLS]


async def all_tools(notes_file: str | Path = DEFAULT_NOTES):
    return LOCAL_TOOLS + await load_mcp_tools(notes_file)
