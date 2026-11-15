# EXER040 — Context Engineering

**Module 8 · Evaluation, Context and Deployment** · Lecture: [Lecture/lectures/lec040.html](../Lecture/lectures/lec040.html)

## Goal

Treat the context window as a budget you design. Measure where the tokens of
a call go, shrink a large tool result two ways (compacting it, and handing it
to a sub-agent), test how a fact's position and the noise around it affect
the answer, and **measure** accuracy and tokens per call for every option.

## The project

A wholesale customer, Bayani Café, asks the support assistant about their
orders. The order lookup tool returns [account.json](account.json): 30 orders,
38 KB, about 14,500 tokens of raw API response. [cases.json](cases.json) has
six questions about those orders, five facts ("needles") about the café, and
1,000 look-alike notes about other customers to use as noise.

Every call is built from the same four sections, in this order:

```text
system  +  tools  +  history  +  tool_result   →   then the question, last
```

| Function | Part | What it must do |
|---|---|---|
| `count_tokens(text)` | Budgeting | Tokens of a piece of text |
| `budget_report(sections)` | Budgeting | Tokens per section, plus the total |
| `fit_to_budget(sections, budget)` | Budgeting | Keep sections in order; cut the first that overflows; empty the rest |
| `compact_orders(account)` | Tool results | One line per order with what support needs |
| `run_subagent(llm, question, material)` | Isolation | Read the material in a separate call; return findings and the tokens used |
| `needle_context(needle, distractors, n, position)` | Position and noise | Put one fact at the start, middle or end of n distractors |
| `evaluate(llm, builder, probes)` | Measuring | Accuracy, main-call tokens, total tokens, and the misses |

## Tasks

Complete the TODOs in `starter/context_engineering.py`. `build_messages`, `recalled`,
`build_strategies`, `noise_sweep` and `main` are given.

## Run it

```bash
uv run python EXER040/starter/context_engineering.py
uv run python EXER040/check.py
```

## Success criteria

- [ ] The script prints the tokens of each section for the raw and the compacted context
- [ ] Cutting the raw response to a 4,000-token budget loses the answers about later orders
- [ ] The compacted context answers as well as the raw dump for a fraction of the tokens
- [ ] The sub-agent keeps the main call small, and the table shows that its total tokens did not go down
- [ ] The noise table shows accuracy and tokens for every amount of noise and every position, and you can say what your model's numbers mean
- [ ] All 7 checks pass (6 offline, 1 calls your model)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Compact by question: keep only the orders the question names, and fall back to the full compact list when it names none. *Done when:* the table has a row for it next to `compacted`, and you can say which question needs the fallback.
2. **Connect (EXER027).** An agent loop re-sends its whole history on every step. Count the input tokens of each step of an 8-step loop when the order lookup goes into the history raw, compacted, or through a sub-agent. *Done when:* the script prints the tokens of every step and the sum for all three, and you can say why the sub-agent's single-call cost is higher but its loop total is lower.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER040/stretch/goal1_question_aware.py
uv run python EXER040/stretch/goal2_agent_loop_growth.py
```
