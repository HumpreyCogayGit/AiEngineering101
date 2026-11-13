"""EXER032 — MCP Concepts and Using a Server.

MCP (Model Context Protocol) is a standard plug between AI apps and tools.
A HOST (your app) runs a CLIENT per SERVER. Servers expose tools, resources
and prompts; any MCP-aware app can use any MCP server.

Part 1 talks to the server with the raw MCP client.
Part 2 loads the same tools into a LangChain agent with langchain-mcp-adapters.

The server is ready-made: EXER032/servers/coffee_server.py — read it first.

    uv run python EXER032/starter/mcp_client.py
    uv run python EXER032/check.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from aicourse.llm import get_chat_model

SERVER = Path(__file__).resolve().parent.parent / "servers" / "coffee_server.py"


# ------------------------------------------------------------------ part 1: raw MCP client
def server_params() -> StdioServerParameters:
    """How to start the server: StdioServerParameters(command=sys.executable, args=[str(SERVER)])
    (sys.executable = the Python running this script, so the server gets the same packages)."""
    # TODO
    raise NotImplementedError("server_params")


async def list_capabilities() -> dict[str, list[str]]:
    """Connect, handshake, and list what the server offers.

    async with stdio_client(server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()           # the MCP handshake
            tools = await session.list_tools()   # .tools -> objects with .name
            ... list_resources() (.resources, each .uri) and list_prompts() (.prompts, each .name)
    Return {"tools": [names], "resources": [str(uri), ...], "prompts": [names]}
    """
    # TODO
    raise NotImplementedError("list_capabilities")


async def call_tool(name: str, arguments: dict) -> str:
    """result = await session.call_tool(name, arguments)

    result.content is a list of content blocks; join the .text of those with type == "text".
    If result.isError is True, return "ERROR: " + text.
    """
    # TODO
    raise NotImplementedError("call_tool")


async def read_resource(uri: str) -> str:
    """result = await session.read_resource(uri); return result.contents[0].text"""
    # TODO
    raise NotImplementedError("read_resource")


# ------------------------------------------------------------------ part 2: LangChain agent
def connections() -> dict:
    """The config MultiServerMCPClient needs — one entry per server:
    {"coffee": {"command": sys.executable, "args": [str(SERVER)], "transport": "stdio"}}"""
    # TODO
    raise NotImplementedError("connections")


async def load_tools():
    """MultiServerMCPClient(connections()) then `await client.get_tools()` → LangChain tools."""
    # TODO
    raise NotImplementedError("load_tools")


async def ask_agent(llm: BaseChatModel, question: str) -> str:
    agent = create_agent(llm, await load_tools(),
                         system_prompt="You are the Nimbus Coffee assistant. Use the tools for facts.")
    result = await agent.ainvoke({"messages": [("user", question)]})  # MCP tools are async: use ainvoke
    return result["messages"][-1].text


async def main() -> None:
    print("Server capabilities:", await list_capabilities())
    print("\nlist_products  ->", await call_tool("list_products", {}))
    print("get_product    ->", await call_tool("get_product", {"name": "Barako Bold"}))
    print("bad product    ->", await call_tool("get_product", {"name": "Starbucks"}))
    print("menu://today   ->", await read_resource("menu://today"))

    tools = await load_tools()
    print("\nAs LangChain tools:", [(t.name, list(t.args)) for t in tools])
    question = "I like chocolatey coffee. Which Nimbus beans should I buy, how much are they, and when is BGC open?"
    print(f"\nQ: {question}\nA: {await ask_agent(get_chat_model(temperature=0), question)}")


if __name__ == "__main__":
    asyncio.run(main())
