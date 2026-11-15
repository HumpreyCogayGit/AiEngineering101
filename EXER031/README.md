# EXER031 — Multi-Agent Systems

**Module 5 · Agents with LangGraph** · Lecture: [Lecture/lectures/lec031.html](../Lecture/lectures/lec031.html)

## Goal

Build a supervisor that coordinates specialist agents, and learn when a team
of agents is worth its extra cost, and when a single agent is better.

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

1. `make_workers`: the two sub-agents
2. `build_team`: the supervisor node (with the "no FINISH before the writer" guard)
   and the worker wrapper
3. `build_handoff_team`: the same two agents with no supervisor: each node returns
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

## Transfer task (end of Module 5)

Optional, and different from the stretch goals: a new problem in a new domain, with **no starter code and no `check.py`**. It shows whether you can use Module 5's ideas without scaffolding.

Build a **library-loans agent** with no starter code. A member can list loans, renew a loan and ask
for a fine to be waived. Loans can be renewed at most twice and never when another member has reserved
the book. Waiving a fine needs a librarian's approval.

- [ ] The renewal rules are enforced inside the tool, not only in the prompt
- [ ] Waiving a fine pauses the agent with `interrupt()` and resumes with the librarian's decision (EXER029)
- [ ] A failure case is part of your run: the member claims a librarian already allowed a third renewal, and the loan is not renewed
- [ ] Every renewal and waiver is written to an audit list, and the script checks the rules held at the end

Reference answer, for after you have tried:

```bash
uv run python EXER031/transfer/reference_library_agent.py
```
