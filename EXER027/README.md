# EXER027 — An Agent from Scratch

**Module 5 · Agents with LangGraph** · Lecture: [Lecture/lectures/lec027.html](../Lecture/lectures/lec027.html)

## Goal

Build the ReAct agent loop yourself as a LangGraph graph (an `agent` node, a
`tools` node and one conditional edge) and protect it from infinite loops.

## Tasks

Complete the TODOs in `starter/react_agent.py`:

1. `should_continue`: the conditional edge
2. `build_agent`: `MessagesState`, the two nodes, the loop
3. `run`: invoke with a `recursion_limit` and handle `GraphRecursionError`

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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a per-run tool budget: after N tool calls the agent must answer with what it has. *Done when:* with a budget of 2, a question that needs four lookups ends with two results and a clear statement of what is missing.
2. **Connect (EXER007).** Stream the agent's tokens as well as its steps. *Done when:* tool steps appear as they finish, and the final answer is written token by token.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER027/stretch/goal1_tool_budget.py
uv run python EXER027/stretch/goal2_stream_tokens.py
```
