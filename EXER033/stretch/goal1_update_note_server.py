"""EXER033 stretch goal 1 — an `update_note` tool with partial updates.

    uv run python EXER033/stretch/goal1_update_note_server.py           # the server (speaks MCP on stdio)
    uv run python EXER033/stretch/goal1_update_note_server.py --demo    # a client that exercises it

"Partial" means: only the fields you pass are changed. Every argument except
the id is optional and defaults to None, and None means "leave it alone".
That gives the model one small tool instead of three (rename, rewrite,
retag), and it cannot wipe a field by forgetting to repeat it.

The server extends the reference solution: importing it registers its tools
on the same FastMCP object, and this file adds one more.
"""

from __future__ import annotations

import sys

from aicourse.stretch import solution_module

base = solution_module(__file__, "notes_server.py")
mcp = base.mcp


@mcp.tool()
def update_note(note_id: str, title: str | None = None, content: str | None = None,
                tags: list[str] | None = None) -> dict:
    """Change a note. Pass only the fields to change; fields you leave out keep their value.
    Returns the updated note."""
    notes = base.load()
    if note_id not in notes:
        raise ValueError(f"No note with id {note_id}. Use list_notes to see valid ids.")
    if title is None and content is None and tags is None:
        raise ValueError("Nothing to update: pass at least one of title, content or tags.")
    note = notes[note_id]
    if title is not None:
        if not title.strip():
            raise ValueError("title must not be empty")
        note["title"] = title.strip()
    if content is not None:
        note["content"] = content
    if tags is not None:  # an empty list is a real value: it removes all tags
        note["tags"] = sorted({t.strip().lower() for t in tags if t.strip()})
    base.save(notes)
    return note


async def demo() -> None:
    import json
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

                async def call(name: str, args: dict) -> str:
                    result = await session.call_tool(name, args)
                    text = "\n".join(c.text for c in result.content if c.type == "text")
                    return f"ERROR: {text}" if result.isError else text

                print("Tools:", [t.name for t in (await session.list_tools()).tools])
                note = json.loads(await call("add_note", {"title": "Beans", "content": "Order Barako.", "tags": ["todo"]}))
                print("added      :", {k: note[k] for k in ("title", "content", "tags")})
                changed = json.loads(await call("update_note", {"note_id": note["id"], "content": "Order Barako and Decaf."}))
                print("new content:", {k: changed[k] for k in ("title", "content", "tags")})
                changed = json.loads(await call("update_note", {"note_id": note["id"], "tags": []}))
                print("no tags    :", {k: changed[k] for k in ("title", "content", "tags")})
                print("no fields  :", await call("update_note", {"note_id": note["id"]}))
                print("bad id     :", await call("update_note", {"note_id": "nope", "title": "x"}))


if __name__ == "__main__":
    if "--demo" in sys.argv:
        import asyncio

        asyncio.run(demo())
    else:
        mcp.run()
