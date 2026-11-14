# EXER039 — Conversation Memory Strategies

**Module 8 · Beyond the Capstone** · Lecture: [Lecture/lectures/lec039.html](../Lecture/lectures/lec039.html)

## Goal

Build the three standard ways to keep a long conversation inside a budget
(trimming, summarizing, retrieving past turns) and **measure** them against
each other on recall and on cost.

## The project

`conversation.json` (given) is a 48-message support conversation with facts
planted early, in the middle and at the end, and six probe questions about
them. Every strategy is a function of the same shape:

```python
strategy(history, question) -> the messages to send
```

| Function | What it must do |
|---|---|
| `count_tokens(messages)` | Estimated tokens of a message list |
| `trim_recent(history, max_tokens)` | The newest messages that fit, starting on a user message |
| `summary_and_recent(history, summary, keep_last)` | One summary message, then the last turns word for word |
| `pair_turns(history)` | Group the history into `[question, answer]` exchanges |
| `retrieve_turns(index, question, k, keep_last)` | The most relevant exchanges plus the latest, oldest first |
| `evaluate(llm, strategy, history, probes)` | Recall, tokens per question, and the questions missed |

## Tasks

Complete the TODOs in `starter/memory_strategies.py`. `summarize`, `TurnIndex`, `ask`
and `build_strategies` are given.

## Run it

```bash
uv run python EXER039/starter/memory_strategies.py
uv run python EXER039/check.py
```

## Success criteria

- [ ] The script prints one row per strategy: recall, tokens per question, and what was missed
- [ ] Trimming to 400 tokens forgets the early facts (order number, allergy, floor)
- [ ] Summarizing and retrieving both recall more than trimming, for less than half the tokens of the full history
- [ ] You can say, for each strategy, what kind of fact it loses
- [ ] All 7 checks pass (6 offline, 1 calls your models)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a hybrid strategy (a short summary plus retrieved exchanges) and compare it with its two halves. *Done when:* the table has a row for the hybrid, and you can say whether its extra tokens bought any recall.
2. **Connect (EXER035).** Count the setup cost of each strategy and find the break-even point against the full history. *Done when:* the script prints setup tokens, tokens per question, and after how many questions each strategy is cheaper.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER039/stretch/goal1_hybrid_strategy.py
uv run python EXER039/stretch/goal2_setup_cost.py
```
