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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Require approval only for refunds above a threshold. *Done when:* a ₱200 refund runs without a pause, and a ₱3,450 refund waits for a decision.
2. **Connect (EXER028).** Persist the pending approval so that the script can be closed and resumed. *Done when:* `start` exits while waiting, and `approve` in a new process finishes the same run.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER029/stretch/goal1_refund_threshold.py
uv run python EXER029/stretch/goal2_resume_later.py start
```
