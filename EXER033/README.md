# EXER033 — Build Your Own MCP Server

**Module 6 · MCP** · Lecture: [Lecture/lectures/lec033.html](../Lecture/lectures/lec033.html)

## Goal

Write an MCP server with the Python MCP SDK (`FastMCP`) that exposes tools, a
resource template and a prompt, usable by any MCP host and not just your code.

## The project

A **notes** server, stored in a JSON file:

| Type | Name |
|---|---|
| Tools | `add_note` (given), `list_notes`, `search_notes`, `delete_note` |
| Resource template | `notes://{note_id}` |
| Prompt | `summarize_notes` |

## Tasks

Complete the TODOs in `starter/notes_server.py`.

## Run it

```bash
uv run python EXER033/check.py        # starts your server and tests it as an MCP client
```

Optional, with Node.js installed: click through your server in the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run python EXER033/starter/notes_server.py
```

## Success criteria

- [ ] All four tools work, and errors come back as error results, not crashes
- [ ] `notes://<id>` returns the note text
- [ ] `summarize_notes` builds a prompt that contains the notes
- [ ] All 6 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add an `update_note` tool with partial updates: only the fields that are passed change. *Done when:* updating the content leaves title and tags alone, and a call with no fields returns an error result.
2. **Connect (EXER032).** Add a resource that lists all notes, and read it from a client. *Done when:* `notes://index` returns id, title and tags of every note, and `notes://<id>` still returns one note.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER033/stretch/goal1_update_note_server.py --demo
uv run python EXER033/stretch/goal2_notes_index_server.py --demo
```
