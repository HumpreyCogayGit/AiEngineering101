"""EXER033 checks: start YOUR server over stdio and test it as a real MCP client would.

Run:  uv run python EXER033/check.py
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from aicourse.check import Checker

checker = Checker(__file__)
SERVER = checker.path("notes_server.py")


async def with_session(fn):
    """Start the server with a fresh, empty notes file and run fn(session)."""
    with tempfile.TemporaryDirectory() as tmp:
        params = StdioServerParameters(
            command=sys.executable, args=[str(SERVER)],
            env={**os.environ, "NOTES_FILE": str(Path(tmp) / "notes.json")},
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await fn(session)


async def call(session, name, args):
    result = await session.call_tool(name, args)
    if result.isError:
        return {"error": " ".join(c.text for c in result.content)}
    if result.structuredContent is not None:
        data = result.structuredContent
        return data.get("result", data) if isinstance(data, dict) and set(data) == {"result"} else data
    return json.loads(result.content[0].text)


def run(fn):
    return asyncio.run(with_session(fn))


@checker.check("the server exposes add_note, list_notes, search_notes and delete_note")
def _():
    async def t(s):
        return {tool.name for tool in (await s.list_tools()).tools}
    names = run(t)
    missing = {"add_note", "list_notes", "search_notes", "delete_note"} - names
    if missing == {"list_notes", "search_notes", "delete_note"}:
        raise NotImplementedError("list_notes, search_notes, delete_note")
    assert not missing, f"missing tools: {missing}"


@checker.check("list_notes filters by tag")
def _():
    async def t(s):
        await call(s, "add_note", {"title": "Groceries", "content": "oat milk", "tags": ["Home"]})
        await call(s, "add_note", {"title": "Sprint", "content": "ship RAG", "tags": ["work"]})
        return await call(s, "list_notes", {}), await call(s, "list_notes", {"tag": "home"})
    everything, home = run(t)
    assert len(everything) == 2 and [n["title"] for n in home] == ["Groceries"], (everything, home)


@checker.check("search_notes is case-insensitive across title and content")
def _():
    async def t(s):
        await call(s, "add_note", {"title": "Coffee order", "content": "Barako Bold x3"})
        await call(s, "add_note", {"title": "Ideas", "content": "a COFFEE quiz"})
        await call(s, "add_note", {"title": "Other", "content": "nothing"})
        return await call(s, "search_notes", {"query": "coffee"})
    assert len(run(t)) == 2


@checker.check("delete_note removes a note; unknown ids give an error result")
def _():
    async def t(s):
        note = await call(s, "add_note", {"title": "Temp", "content": "x"})
        deleted = await call(s, "delete_note", {"note_id": note["id"]})
        missing = await call(s, "delete_note", {"note_id": "nope"})
        return deleted, missing, await call(s, "list_notes", {})
    deleted, missing, remaining = run(t)
    assert "Temp" in str(deleted) and "error" in missing and remaining == [], (deleted, missing, remaining)


@checker.check("resource template notes://{note_id} returns the note text")
def _():
    async def t(s):
        templates = [str(x.uriTemplate) for x in (await s.list_resource_templates()).resourceTemplates]
        note = await call(s, "add_note", {"title": "Recipe", "content": "1:16 ratio", "tags": ["coffee"]})
        content = await s.read_resource(f"notes://{note['id']}")
        return templates, content.contents[0].text
    templates, text = run(t)
    assert "notes://{note_id}" in templates, templates
    assert text.startswith("# Recipe") and "1:16 ratio" in text and "coffee" in text, text


@checker.check("prompt summarize_notes includes the notes")
def _():
    async def t(s):
        await call(s, "add_note", {"title": "Plan", "content": "launch ube latte", "tags": ["work"]})
        prompts = [p.name for p in (await s.list_prompts()).prompts]
        result = await s.get_prompt("summarize_notes", {"tag": "work"})
        return prompts, result.messages[0].content.text
    prompts, text = run(t)
    assert "summarize_notes" in prompts and "launch ube latte" in text, (prompts, text)


checker.run()
