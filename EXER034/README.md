# EXER034 — Agent with Multiple MCP Servers

**Module 6 · MCP** · Lecture: [Lecture/lectures/lec034.html](../Lecture/lectures/lec034.html)

## Goal

Connect one agent to several MCP servers at once, and handle what that brings:
tool name clashes, least-privilege allowlists, passing configuration to
servers, and auditing every tool call.

## The servers

[servers/](servers/) contains the coffee server (EXER032) and the notes server (EXER033).

## Tasks

Complete the TODOs in `starter/multi_server_agent.py`:

1. `ALLOWED_TOOLS` — everything the assistant needs, nothing more
2. `connections` — two stdio servers; pass `NOTES_FILE` through `env`
3. `load_tools` — prefixed names + allowlist filter
4. `AuditLog.on_tool_start`

## Run it

```bash
uv run python EXER034/starter/multi_server_agent.py
uv run python EXER034/check.py
```

## Success criteria

- [ ] The agent looks up products (coffee server) and saves notes (notes server) in one task
- [ ] "Delete all my notes" fails because the delete tool was never given to the agent
- [ ] The audit log lists every tool call
- [ ] All 5 checks pass
