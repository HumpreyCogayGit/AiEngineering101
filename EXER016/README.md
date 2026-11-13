# EXER016 — Tool Calling by Hand

**Module 3 · Tool Calling** · Lecture: [Lecture/lectures/lec016.html](../Lecture/lectures/lec016.html)

## Goal

Understand tool (function) calling from first principles: tool schemas, the
`tool_calls` message, `tool` result messages, and the loop that ties them together.

## The project

An assistant with two tools: `get_weather(city)` (fake data) and `calculate(expression)`
(a safe arithmetic evaluator — never `eval()`).

## Tasks

Complete the TODOs in `starter/tools_raw.py`:

1. `TOOLS` — JSON schemas describing both tools
2. `run_tool` — dispatch by name, return results **and errors** as JSON strings
3. `run_conversation` — the tool-calling loop with a round limit

## Run it

```bash
uv run python EXER016/starter/tools_raw.py
uv run python EXER016/check.py
```

## Success criteria

- [ ] Weather questions call `get_weather`; math questions call `calculate`
- [ ] "Is it warmer in Manila or London?" triggers **two** tool calls in one turn
- [ ] The otter question is answered without any tool
- [ ] All 6 checks pass
