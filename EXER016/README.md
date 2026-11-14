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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a `get_time(timezone)` tool, and ask a question that needs two different tools. *Done when:* the verbose trace shows `get_time` and another tool being called for one question.
2. **Connect (EXER011).** Run the tool calls of one round concurrently. *Done when:* four slow tool calls take about as long as one, and the tool messages are still in request order.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER016/stretch/goal1_time_tool.py
uv run python EXER016/stretch/goal2_concurrent_tools.py
```
