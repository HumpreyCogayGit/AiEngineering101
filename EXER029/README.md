# EXER029 — Human in the Loop

**Module 5 · Agents with LangGraph** · Lecture: [Lecture/lectures/lec029.html](../Lecture/lectures/lec029.html)

## Goal

Pause an agent before risky actions, let a human approve, edit or reject them,
and resume — using `interrupt()`, `Command(resume=...)` and a checkpointer.

## The project

A support-inbox agent that can read emails (safe), and send emails or issue
refunds (risky, so they need approval).

```
START → agent ─┬→ review ─┬→ tools → agent ...
               │   (interrupt)  └→ agent (rejected)
               └→ END
```

## Tasks

Complete the TODOs in `starter/hitl_agent.py`: the `review` node, `pending`
and `resume`.

## Run it

```bash
uv run python EXER029/starter/hitl_agent.py
uv run python EXER029/check.py
```

## Success criteria

- [ ] Reading the inbox happens without asking
- [ ] Every email and refund waits for your decision
- [ ] Approve, edit and reject each behave correctly
- [ ] All 5 checks pass (offline)
