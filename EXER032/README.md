# EXER032 — MCP Concepts and Using a Server

**Module 6 · MCP** · Lecture: [Lecture/lectures/lec032.html](../Lecture/lectures/lec032.html)

## Goal

Understand the Model Context Protocol — hosts, clients, servers, transports,
and the three capability types (tools, resources, prompts) — by talking to an
MCP server directly, then handing its tools to a LangChain agent.

## The server

[servers/coffee_server.py](servers/coffee_server.py) is ready-made. It
exposes 3 tools, 1 resource and 1 prompt over **stdio**. Read it first.

Optional — explore it visually with the MCP Inspector (needs Node.js):

```bash
npx @modelcontextprotocol/inspector uv run python EXER032/servers/coffee_server.py
```

## Tasks

Complete the TODOs in `starter/mcp_client.py`:

1. Part 1 (raw MCP): `server_params`, `list_capabilities`, `call_tool`, `read_resource`
2. Part 2 (LangChain): `connections`, `load_tools`

## Run it

```bash
uv run python EXER032/starter/mcp_client.py
uv run python EXER032/check.py
```

## Success criteria

- [ ] The script lists the server's tools, resources and prompts
- [ ] A bad product name returns a readable error, not a crash
- [ ] The agent answers a multi-part question by calling several MCP tools
- [ ] All 7 checks pass
