"""EXER034 stretch goal 2 — a third server, and a tool-name collision.

    uv run python EXER034/stretch/goal2_name_collision.py

inventory_server.py (next to this file) has a tool called `list_products`.
So does the coffee server. Loaded WITHOUT prefixes, the agent gets two tools
with one name: the model cannot tell them apart, and providers reject a
request that defines the same function twice. Loaded WITH
`tool_name_prefix=True` they become coffee_list_products and
inventory_list_products, and the agent can use both in one answer.
"""

from __future__ import annotations

import asyncio
import sys
from collections import Counter
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "multi_server_agent.py")

INVENTORY_SERVER = Path(__file__).resolve().parent / "inventory_server.py"
ALLOWED = base.ALLOWED_TOOLS | {"inventory_list_products", "inventory_get_stock"}


def connections() -> dict:
    return {
        **base.connections(),
        "inventory": {"command": sys.executable, "args": [str(INVENTORY_SERVER)], "transport": "stdio"},
    }


async def load(prefix: bool) -> list:
    return await MultiServerMCPClient(connections(), tool_name_prefix=prefix).get_tools()


def collisions(tools: list) -> list[str]:
    return sorted(name for name, count in Counter(t.name for t in tools).items() if count > 1)


async def main() -> None:
    plain = await load(prefix=False)
    print(f"Without prefixes: {len(plain)} tools, colliding names: {collisions(plain)}")
    for tool in plain:
        if tool.name in collisions(plain):
            print(f"  {tool.name}: {tool.description}")

    prefixed = [t for t in await load(prefix=True) if t.name in ALLOWED]
    print(f"\nWith prefixes: {len(prefixed)} tools, colliding names: {collisions(prefixed)}")
    print(" ", sorted(t.name for t in prefixed))

    agent = base.build_agent(get_chat_model(temperature=0), prefixed)
    audit = base.AuditLog()
    question = "Which of our coffees are out of stock or below 5 bags, and what does each of those cost?"
    print(f"\nQ: {question}\nA: {await base.ask(agent, question, audit=audit)}")
    print("\nServers used:", sorted({call["tool"].split("_")[0] for call in audit.calls}))
    for call in audit.calls:
        print(f"  {call['tool']}  {call['input'][:60]}")


if __name__ == "__main__":
    asyncio.run(main())
