# EXER038 — Evaluating Agents

**Module 8 · Evaluation, Context and Deployment** · Lecture: [Lecture/lectures/lec038.html](../Lecture/lectures/lec038.html)

## Goal

Score what an agent **did**, not only what it said. You build a scorer for
tool-call *trajectories* that answers three questions about a run: did it call
the right tools, in a workable order, with the right arguments?

## The project

`agent_under_test.py` (given) is a small order assistant with three tools.
`cases.json` (given) holds six questions, each with the tool calls a correct run
makes and the keywords a correct answer contains. You write the scorer.

| Function | What it must do |
|---|---|
| `extract_trajectory(messages)` | List every tool call of a run as `Call(name, args)`, in order |
| `missing_and_extra(actual, expected)` | Compare tool names as multisets: what is missing, what is extra |
| `in_order(actual, expected)` | Is `expected` a subsequence of `actual`? |
| `args_match(actual, expected)` | Does every expected argument have a matching value? |
| `score_trajectory(actual, expected)` | One verdict per question, plus readable problems |
| `summarize(rows)` | The share of cases that passed each check |

## Tasks

Complete the TODOs in `starter/trajectory_eval.py`. `value_matches`, `unmatched_calls`,
`run_case` and the report are given: read them first.

## Run it

```bash
uv run python EXER038/starter/trajectory_eval.py     # runs the six cases and writes a report
uv run python EXER038/check.py
```

## Success criteria

- [ ] The script prints PASS or FAIL per case with the trajectory, and writes `output/agent_eval.md`
- [ ] An agent that gives the right answer without calling its tools FAILS (the check proves it with a scripted model)
- [ ] `3*390 + 2*520` and `1170 + 1040` both count as the right calculator argument
- [ ] Every failed case says what was wrong: a missing call, an extra call, a wrong order or wrong arguments
- [ ] All 8 checks pass (7 offline, 1 calls your model)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add an efficiency score: flag redundant calls (same tool, same arguments) and runs that used more calls than expected. *Done when:* three hand-written runs that all reach the right answer get efficiency 1.0, 0.5 and 0.5, with each redundant call named.
2. **Connect (EXER037).** Score the trajectories of the capstone assistant with your scorer. *Done when:* for three capstone questions the script prints the trajectory, what is missing or extra, and whether it is in order.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER038/stretch/goal1_efficiency.py
uv run python EXER038/stretch/goal2_score_capstone.py
```
