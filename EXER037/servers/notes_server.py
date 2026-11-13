"""Notes MCP server (the EXER033 solution, copied here so EXER037 is self-contained).

A notes server any MCP host (your agents, Claude Desktop, VS Code, ...) can use.

    uv run python EXER037/servers/notes_server.py          # speaks MCP on stdio
    npx @modelcontextprotocol/inspector uv run python EXER037/servers/notes_server.py

Notes are stored in a JSON file (NOTES_FILE env var, default: output/notes.json).
Never print() to stdout in a stdio server — stdout carries the protocol.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DEFAULT_FILE = Path(__file__).resolve().parent / "output" / "notes.json"
mcp = FastMCP("notes", log_level="WARNING")


# ------------------------------------------------------------------ storage
def store_path() -> Path:
    return Path(os.environ.get("NOTES_FILE", DEFAULT_FILE))


def load() -> dict[str, dict]:
    path = store_path()
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save(notes: dict[str, dict]) -> None:
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")


def summary(note: dict) -> dict:
    return {"id": note["id"], "title": note["title"], "tags": note["tags"]}


# ------------------------------------------------------------------ tools
@mcp.tool()
def add_note(title: str, content: str, tags: list[str] | None = None) -> dict:
    """Create a note. Returns the new note with its id."""
    if not title.strip():
        raise ValueError("title must not be empty")
    notes = load()
    note = {
        "id": uuid.uuid4().hex[:8],
        "title": title.strip(),
        "content": content,
        "tags": sorted({t.strip().lower() for t in (tags or []) if t.strip()}),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    notes[note["id"]] = note
    save(notes)
    return note


@mcp.tool()
def list_notes(tag: str | None = None) -> list[dict]:
    """List notes (id, title, tags), optionally only those with a given tag."""
    notes = load().values()
    if tag:
        notes = [n for n in notes if tag.lower() in n["tags"]]
    return [summary(n) for n in notes]


@mcp.tool()
def search_notes(query: str) -> list[dict]:
    """Find notes whose title or content contains the query (case-insensitive)."""
    q = query.lower()
    return [summary(n) for n in load().values() if q in n["title"].lower() or q in n["content"].lower()]


@mcp.tool()
def delete_note(note_id: str) -> str:
    """Delete a note by id."""
    notes = load()
    if note_id not in notes:
        raise ValueError(f"No note with id {note_id}. Use list_notes to see valid ids.")
    title = notes.pop(note_id)["title"]
    save(notes)
    return f"Deleted note '{title}'"


# ------------------------------------------------------------------ resources
@mcp.resource("notes://{note_id}")
def read_note(note_id: str) -> str:
    """The full text of one note."""
    note = load().get(note_id)
    if note is None:
        raise ValueError(f"No note with id {note_id}. Use list_notes to see valid ids.")
    return f"# {note['title']}\nTags: {', '.join(note['tags']) or '-'}\n\n{note['content']}"


# ------------------------------------------------------------------ prompts
@mcp.prompt()
def summarize_notes(tag: str = "") -> str:
    """Ask the model to summarize all notes (optionally only one tag)."""
    notes = [n for n in load().values() if not tag or tag.lower() in n["tags"]]
    body = "\n\n".join(f"## {n['title']}\n{n['content']}" for n in notes) or "(no notes)"
    return f"Summarize these notes as 3–5 bullet points and list any action items:\n\n{body}"


if __name__ == "__main__":
    mcp.run()
