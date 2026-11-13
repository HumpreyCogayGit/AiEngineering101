# EXER026 — LangGraph Basics

**Module 5 · Agents with LangGraph** · Lecture: [Lecture/lectures/lec026.html](../Lecture/lectures/lec026.html)

## Goal

Learn LangGraph's building blocks without an LLM in the way: state, reducers,
nodes, normal edges, conditional edges, streaming, and drawing the graph.

## The project

A support-ticket router: classify → prioritize → route to a handler →
escalate if urgent.

```
START → classify → prioritize ─┬→ billing   ─┬→ escalate → END
                               ├→ technical ─┤
                               └→ general   ─┴→ END
```

## Tasks

Complete the TODOs in `starter/ticket_graph.py`: the `steps` reducer,
`classify`, `prioritize`, both routers, and `build_graph`.

## Run it

```bash
uv run python EXER026/starter/ticket_graph.py
uv run python EXER026/check.py
```

## Success criteria

- [ ] The script prints a Mermaid diagram of your graph
- [ ] `steps` shows the exact path each ticket took
- [ ] Urgent tickets pass through `escalate`; normal ones don't
- [ ] All 6 checks pass (offline)
