"""EXER032 stretch goal 2 — connect to a second MCP server and list its capabilities.

    uv run python EXER032/stretch/goal2_second_server.py
    uv run python EXER032/stretch/goal2_second_server.py npx -y @modelcontextprotocol/server-everything

The client code does not care which server it talks to: give it a command and
it performs the same handshake and discovery. That is the whole point of a
protocol.

With no arguments it starts the notes server from EXER033 (already on your
disk). With arguments it starts that command instead. The second example line
runs the public reference server published by the MCP project; it needs
Node.js and downloads the package from npm, so read what you are about to run
first: a server you start is a program with your user's permissions (EXER034).
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

NOTES_SERVER = Path(__file__).resolve().parents[2] / "EXER033" / "solution" / "notes_server.py"


async def describe_server(params: StdioServerParameters) -> dict:
    """Handshake + discovery for ANY stdio server. A server may not offer every capability type."""
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            info = await session.initialize()
            found: dict = {"name": info.serverInfo.name, "version": info.serverInfo.version}
            offered = info.capabilities
            if offered.tools:
                found["tools"] = {t.name: (t.description or "").strip().split("\n")[0]
                                  for t in (await session.list_tools()).tools}
            if offered.resources:
                found["resources"] = [str(r.uri) for r in (await session.list_resources()).resources]
                found["resource templates"] = [
                    t.uriTemplate for t in (await session.list_resource_templates()).resourceTemplates]
            if offered.prompts:
                found["prompts"] = [p.name for p in (await session.list_prompts()).prompts]
            return found


def print_capabilities(found: dict) -> None:
    print(f"Server: {found['name']} {found['version']}")
    for name, description in found.get("tools", {}).items():
        print(f"  {'tool':<18} {name:<16} {description[:60]}")
    for kind in ("resources", "resource templates", "prompts"):
        for item in found.get(kind, []):
            print(f"  {kind.rstrip('s'):<18} {item}")


async def main() -> None:
    if len(sys.argv) > 1:
        params = StdioServerParameters(command=sys.argv[1], args=sys.argv[2:])
        print_capabilities(await describe_server(params))
        return
    with tempfile.TemporaryDirectory() as tmp:  # an empty notes file that disappears afterwards
        params = StdioServerParameters(command=sys.executable, args=[str(NOTES_SERVER)],
                                       env={**os.environ, "NOTES_FILE": str(Path(tmp) / "notes.json")})
        print_capabilities(await describe_server(params))


if __name__ == "__main__":
    asyncio.run(main())
