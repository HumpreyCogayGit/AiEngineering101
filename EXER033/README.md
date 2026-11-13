# EXER033 — Build Your Own MCP Server

**Module 6 · MCP** · Lecture: [Lecture/lectures/lec033.html](../Lecture/lectures/lec033.html)

## Goal

Write an MCP server with the Python MCP SDK (`FastMCP`) that exposes tools, a
resource template and a prompt — usable by any MCP host, not just your code.

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

Optional, with Node.js installed — click through your server in the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run python EXER033/starter/notes_server.py
```

## Success criteria

- [ ] All four tools work, and errors come back as error results, not crashes
- [ ] `notes://<id>` returns the note text
- [ ] `summarize_notes` builds a prompt that contains the notes
- [ ] All 6 checks pass

**Bonus:** add the server to an MCP host you use (e.g. Claude Desktop or VS Code) and let it take notes for you.
