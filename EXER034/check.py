"""EXER034 checks. Run:  uv run python EXER034/check.py"""

import asyncio
import json
import tempfile
from pathlib import Path

from langchain_core.messages import AIMessage

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("multi_server_agent.py")


@checker.check("connections() defines the coffee and notes servers, passing NOTES_FILE")
def _():
    conns = mod.connections("/tmp/my-notes.json")
    assert set(conns) == {"coffee", "notes"}, set(conns)
    assert all(c["transport"] == "stdio" for c in conns.values())
    assert conns["notes"]["env"]["NOTES_FILE"] == "/tmp/my-notes.json"
    assert "PATH" in conns["notes"]["env"], "copy os.environ into env"


@checker.check("ALLOWED_TOOLS = everything except notes_delete_note (least privilege)")
def _():
    assert mod.ALLOWED_TOOLS, "fill in ALLOWED_TOOLS"
    assert "notes_delete_note" not in mod.ALLOWED_TOOLS
    assert {"coffee_get_product", "notes_add_note", "notes_search_notes"} <= mod.ALLOWED_TOOLS


@checker.check("load_tools() prefixes names by server and filters by the allowlist")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        all_tools = asyncio.run(mod.load_tools(Path(tmp) / "n.json", allowed=None))
        allowed = asyncio.run(mod.load_tools(Path(tmp) / "n.json"))
    names = {t.name for t in all_tools}
    assert "coffee_get_product" in names and "notes_delete_note" in names, names
    assert {t.name for t in allowed} == mod.ALLOWED_TOOLS, {t.name for t in allowed}


@checker.check("AuditLog records the tools an agent calls (tools from two servers)")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        notes_file = Path(tmp) / "n.json"
        tools = asyncio.run(mod.load_tools(notes_file))
        llm = fake_chat_model(
            AIMessage(content="", tool_calls=[{"name": "coffee_get_product", "args": {"name": "Barako Bold"}, "id": "a"}]),
            AIMessage(content="", tool_calls=[{"name": "notes_add_note", "args": {"title": "Barako", "content": "₱390"}, "id": "b"}]),
            "Saved.",
        )
        audit = mod.AuditLog()
        answer = asyncio.run(mod.ask(mod.build_agent(llm, tools), "save price", audit=audit))
        saved = json.loads(notes_file.read_text())
    assert answer == "Saved."
    assert [c["tool"] for c in audit.calls] == ["coffee_get_product", "notes_add_note"], audit.calls
    assert [n["title"] for n in saved.values()] == ["Barako"], "the note was not written by the notes server"


@checker.check("a real agent combines both servers  [live API]")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        notes_file = Path(tmp) / "n.json"
        agent = mod.build_agent(get_chat_model(temperature=0), asyncio.run(mod.load_tools(notes_file)))
        asyncio.run(mod.ask(agent, "Look up the price of Barako Bold and save it in a note titled 'Barako price'."))
        saved = json.loads(notes_file.read_text()) if notes_file.exists() else {}
    assert any("390" in n["content"] for n in saved.values()), saved


checker.run()
