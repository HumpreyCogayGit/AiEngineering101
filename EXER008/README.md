# EXER008 — Prompt Engineering Basics

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec008.html](../Lecture/lectures/lec008.html)

## Goal

Learn the prompt techniques that matter most (clear instructions, a fixed
output format, delimiters and few-shot examples) and **measure** their effect
instead of guessing.

## The project

A support-ticket classifier with four labels: `billing`, `technical`, `account`,
`other`. [tickets.json](tickets.json) has 16 labelled tickets to test against.

## Tasks

Complete the TODOs in `starter/prompts.py`:

1. `SYSTEM_V2` + `build_messages_v2`: instructions, label definitions, `<ticket>` delimiters
2. `FEW_SHOT_EXAMPLES` + `build_messages_v3`: add worked examples as message pairs
3. `normalize_label` and `classify`

## Run it

```bash
uv run python EXER008/starter/prompts.py
uv run python EXER008/check.py
```

## Success criteria

- [ ] The script prints accuracy for v1, v2 and v3
- [ ] v1 often answers with a sentence instead of a label (accuracy is low)
- [ ] v3 reaches at least 80% accuracy
- [ ] Your few-shot examples do not appear in the test set
- [ ] All 7 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a fourth prompt version that gives a one-sentence reason before its label, and measure it. *Done when:* the script prints the accuracy of v4 next to v3, with the reason for every miss.
2. **Connect (EXER024).** Print a confusion matrix (expected label against predicted label), not only accuracy. *Done when:* you can read from the table which label is mistaken for which.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER008/stretch/goal1_explain_label.py
uv run python EXER008/stretch/goal2_confusion_matrix.py
```
