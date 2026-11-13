# EXER027 — An Agent from Scratch

**Module 5 · Agents with LangGraph** · Lecture: [Lecture/lectures/lec027.html](../Lecture/lectures/lec027.html)

## Goal

Build the ReAct agent loop yourself as a LangGraph graph — an `agent` node, a
`tools` node and one conditional edge — and protect it from infinite loops.

## Tasks

Complete the TODOs in `starter/react_agent.py`:

1. `should_continue` — the conditional edge
2. `build_agent` — `MessagesState`, the two nodes, the loop
3. `run` — invoke with a `recursion_limit` and handle `GraphRecursionError`

## Run it

```bash
uv run python EXER027/starter/react_agent.py
uv run python EXER027/check.py
```

## Success criteria

- [ ] The script prints each step: tool calls, tool results and the final answer
- [ ] The order total (₱2,210) is computed by tools, not by the model's mental math
- [ ] A model that never stops calling tools is halted by the recursion limit
- [ ] All 6 checks pass
