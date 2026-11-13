"""EXER033 — Build Your Own MCP Server.

A notes server any MCP host (your agents, Claude Desktop, VS Code, ...) can use.

    uv run python EXER033/starter/notes_server.py          # speaks MCP on stdio (waits for a client)
    npx @modelcontextprotocol/inspector uv run python EXER033/starter/notes_server.py
    uv run python EXER033/check.py

Notes are stored in a JSON file (NOTES_FILE env var, default: output/notes.json).
Never print() to stdout in a stdio server — stdout carries the protocol.

FastMCP builds each tool's JSON schema from the type hints and the docstring
(just like @tool in LangChain), so write both carefully.
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


# ------------------------------------------------------------------ storage (given)
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


# TODO: a tool `list_notes(tag: str | None = None) -> list[dict]`
#   "List notes (id, title, tags), optionally only those with a given tag."
#   Return [summary(n) ...]; when tag is given keep only notes whose n["tags"] contains tag.lower()


# TODO: a tool `search_notes(query: str) -> list[dict]`
#   "Find notes whose title or content contains the query (case-insensitive)."


# TODO: a tool `delete_note(note_id: str) -> str`
#   Raise ValueError(f"No note with id {note_id}. Use list_notes to see valid ids.") for unknown ids — FastMCP turns it into
#   an error result the model can read. Otherwise remove it, save, return "Deleted note '<title>'".


# ------------------------------------------------------------------ resources
# TODO: a RESOURCE TEMPLATE @mcp.resource("notes://{note_id}") def read_note(note_id: str) -> str
#   The {note_id} in the URI becomes the function argument.
#   Return "# <title>\nTags: <tags comma separated or ->\n\n<content>"; ValueError for unknown ids.


# ------------------------------------------------------------------ prompts
# TODO: a PROMPT @mcp.prompt() def summarize_notes(tag: str = "") -> str
#   "Ask the model to summarize all notes (optionally only one tag)."
#   Return "Summarize these notes as 3–5 bullet points and list any action items:\n\n" followed by
#   each note as "## <title>\n<content>" (separated by blank lines), or "(no notes)".


if __name__ == "__main__":
    mcp.run()
