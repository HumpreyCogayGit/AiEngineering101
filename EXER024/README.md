# EXER024 — Evaluating RAG

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec024.html](../Lecture/lectures/lec024.html)

## Goal

Measure a RAG system properly: retrieval metrics (hit rate, MRR), generation
metrics scored by an LLM judge (faithfulness, correctness), and refusal
behaviour on unanswerable questions.

## The data

[data/eval_questions.json](../data/eval_questions.json): 20 "golden" questions
with the expected source and a reference answer. One question is deliberately
unanswerable.

## Tasks

Complete the TODOs in `starter/evaluate.py`:

1. `reciprocal_rank`
2. the `Grade` model and `CORRECTNESS_PROMPT`
3. `judge`: LLM-as-judge with structured output
4. `summarize`

## Run it

```bash
uv run python EXER024/starter/evaluate.py
uv run python EXER024/check.py
```

The report is written to `EXER024/starter/output/eval_report.md`.

## Success criteria

- [ ] The run produces a Markdown report with metrics and a per-question table
- [ ] Hit rate ≥ 0.85, faithfulness ≥ 4.0, refusal rate = 1.0
- [ ] You looked at the lowest-scoring rows and can say *why* they failed
- [ ] All 6 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend: calibrate the judge.** Grade the 18 human-labelled answers in [stretch/human_labels.json](stretch/human_labels.json) twice each. Report how often the judge agrees with itself, and its exact and within-one-point agreement with the human scores, per metric and per kind of answer. *Done when:* the script prints those numbers and you can name the kind of answer the judge scores worst.
2. **Connect (EXER023).** Evaluate the RAG chain with the best EXER023 retriever and compare both reports. *Done when:* two reports are written and one table shows every metric for both retrievers.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER024/stretch/goal1_judge_calibration.py
uv run python EXER024/stretch/goal2_compare_retrievers.py
```
