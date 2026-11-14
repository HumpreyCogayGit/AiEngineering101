"""EXER033 stretch goal 2 — a resource that lists all notes, read from a client (EXER032).

    uv run python EXER033/stretch/goal2_notes_index_server.py           # the server
    uv run python EXER033/stretch/goal2_notes_index_server.py --demo    # a client, as in EXER032

`list_notes` is a TOOL: the model decides to call it. `notes://index` is a
RESOURCE: the application decides to load it, for example to show the user
their notes or to put the list into the context before the model starts.
Same data, different controller.

`notes://index` is a fixed URI and `notes://{note_id}` is a template. A fixed
resource is matched first, so a note can never be mistaken for the index.
"""

from __future__ import annotations

import json
import sys

from aicourse.stretch import solution_module

base = solution_module(__file__, "notes_server.py")
mcp = base.mcp


@mcp.resource("notes://index", mime_type="application/json")
def notes_index() -> str:
    """Every note as id, title and tags (no content). Read notes://<id> for the full text."""
    return json.dumps([base.summary(note) for note in base.load().values()], ensure_ascii=False)


async def demo() -> None:
    import os
    import tempfile
    from pathlib import Path

    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    with tempfile.TemporaryDirectory() as tmp:
        params = StdioServerParameters(command=sys.executable, args=[__file__],
                                       env={**os.environ, "NOTES_FILE": str(Path(tmp) / "notes.json")})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for title, tags in (("Bean comparison", ["menu"]), ("Call the roastery", ["todo"])):
                    await session.call_tool("add_note", {"title": title, "content": "...", "tags": tags})

                print("Fixed resources   :", [str(r.uri) for r in (await session.list_resources()).resources])
                print("Resource templates:",
                      [t.uriTemplate for t in (await session.list_resource_templates()).resourceTemplates])

                index = json.loads((await session.read_resource("notes://index")).contents[0].text)
                print("\nnotes://index ->")
                for entry in index:
                    print(f"  {entry['id']}  {entry['title']:<20} {entry['tags']}")
                first = index[0]["id"]
                print(f"\nnotes://{first} ->")
                print("  " + (await session.read_resource(f"notes://{first}")).contents[0].text.replace("\n", "\n  "))


if __name__ == "__main__":
    if "--demo" in sys.argv:
        import asyncio

        asyncio.run(demo())
    else:
        mcp.run()
