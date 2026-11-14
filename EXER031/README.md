# EXER031 — Multi-Agent Systems

**Module 5 · Agents with LangGraph** · Lecture: [Lecture/lectures/lec031.html](../Lecture/lectures/lec031.html)

## Goal

Build a supervisor that coordinates specialist agents, and learn when a team
of agents is worth its extra cost — and when a single agent is better.

## The project

A support team: a **researcher** (searches company documents), a **writer**
(drafts the customer reply), and a **supervisor** who decides who works next.

```
START → supervisor ─┬→ researcher ─┐
            ↑       ├→ writer ─────┤
            └───────┴──────────────┘
                    └→ END (FINISH)
```

## Tasks

Complete the TODOs in `starter/team.py`:

1. `make_workers` — the two sub-agents
2. `build_team` — the supervisor node (with the "no FINISH before the writer" guard)
   and the worker wrapper
3. `build_handoff_team` — the same two agents with no supervisor: each node returns
   `Command(goto=..., update=...)` to pass control directly

## Run it

```bash
uv run python EXER031/starter/team.py
uv run python EXER031/check.py
```

## Success criteria

- [ ] The trace shows supervisor decisions and each worker's output
- [ ] The final reply answers both questions (broken grinder, dog) from the documents
- [ ] A supervisor that never says FINISH is stopped by `MAX_STEPS`, and one that says
      FINISH too early is sent back to the missing worker
- [ ] The handoff team produces the same reply in fewer steps
- [ ] All 10 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a reviewer agent that can send the draft back to the writer once. *Done when:* with a reviewer that never approves, the steps end at `writer -> reviewer -> writer -> reviewer`.
2. **Connect (EXER035).** Count model calls and tokens for the supervisor team and the handoff team. *Done when:* one table compares calls, tokens, seconds and cost of the two teams on the same request.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER031/stretch/goal1_reviewer.py
uv run python EXER031/stretch/goal2_count_calls.py
```
