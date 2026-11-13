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
    # TODO: search get_vector_store() for the 4 most similar chunks and return format_docs(docs)
    #       (or "No matching documents." when nothing is found)
    raise NotImplementedError("search_knowledge_base")


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
    """Connect to servers/notes_server.py over stdio (pass NOTES_FILE via env, as in EXER034),
    with tool_name_prefix=True, and return only the tools in ALLOWED_MCP_TOOLS."""
    # TODO
    raise NotImplementedError("load_mcp_tools")


async def all_tools(notes_file: str | Path = DEFAULT_NOTES):
    return LOCAL_TOOLS + await load_mcp_tools(notes_file)
