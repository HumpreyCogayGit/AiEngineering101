"""EXER032 stretch goal 1 — use the server's prompt as the agent's system prompt.

    uv run python EXER032/stretch/goal1_server_prompt.py
    uv run python EXER032/stretch/goal1_server_prompt.py "bright, fruity coffee"

Prompts are the third MCP capability, and the one the exercise only lists.
A prompt is a template that lives on the SERVER: the team that owns the tools
also ships the instructions that use them well. The client fills in the
arguments (`get_prompt`) and gets finished messages back. Here that text
becomes the system prompt of the agent that uses the same server's tools.
"""

from __future__ import annotations

import asyncio
import sys

from langchain.agents import create_agent
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "mcp_client.py")


async def get_prompt_text(name: str, arguments: dict[str, str]) -> str:
    """Ask the server to fill in one of its prompt templates."""
    async with stdio_client(base.server_params()) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.get_prompt(name, arguments)
            # A prompt is a list of messages; this server's template has one text message.
            return "\n".join(m.content.text for m in result.messages if m.content.type == "text")


async def main() -> None:
    taste = sys.argv[1] if len(sys.argv) > 1 else "chocolatey, low-acid coffee"
    system_prompt = await get_prompt_text("barista_recommendation", {"taste": taste})
    print(f"Prompt from the server:\n  {system_prompt}\n")

    agent = create_agent(get_chat_model(temperature=0), await base.load_tools(), system_prompt=system_prompt)
    result = await agent.ainvoke({"messages": [("user", "What should I buy?")]})
    used = [call["name"] for m in result["messages"] for call in getattr(m, "tool_calls", None) or []]
    print("Tools the agent used:", used)
    print("A:", result["messages"][-1].text)


if __name__ == "__main__":
    asyncio.run(main())
