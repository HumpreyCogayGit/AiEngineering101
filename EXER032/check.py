"""EXER032 checks. Run:  uv run python EXER032/check.py

The first checks start the MCP server for real (no LLM needed).
"""

import asyncio
import json

from aicourse.check import Checker
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("mcp_client.py")


@checker.check("server_params() starts the coffee server with this Python")
def _():
    import sys
    p = mod.server_params()
    assert p.command == sys.executable and p.args[0].endswith("coffee_server.py"), p


@checker.check("list_capabilities() finds 3 tools, 1 resource and 1 prompt")
def _():
    caps = asyncio.run(mod.list_capabilities())
    assert set(caps["tools"]) == {"list_products", "get_product", "store_hours"}, caps
    assert caps["resources"] == ["menu://today"] and caps["prompts"] == ["barista_recommendation"], caps


@checker.check("call_tool() returns the tool result as text")
def _():
    out = asyncio.run(mod.call_tool("get_product", {"name": "Barako Bold"}))
    assert json.loads(out)["price"] == 390, out


@checker.check("call_tool() reports tool errors instead of crashing")
def _():
    out = asyncio.run(mod.call_tool("get_product", {"name": "Nope"}))
    assert out.startswith("ERROR") and "Unknown product" in out, out


@checker.check("read_resource() reads menu://today")
def _():
    assert "Ube Cold Brew" in asyncio.run(mod.read_resource("menu://today"))


@checker.check("load_tools() turns MCP tools into LangChain tools")
def _():
    tools = asyncio.run(mod.load_tools())
    by_name = {t.name: t for t in tools}
    assert set(by_name) == {"list_products", "get_product", "store_hours"}, set(by_name)
    assert "name" in by_name["get_product"].args


@checker.check("an agent answers with MCP tools  [live API]")
def _():
    answer = asyncio.run(mod.ask_agent(get_chat_model(temperature=0), "How much is Barako Bold?"))
    assert "390" in answer, answer


checker.run()
