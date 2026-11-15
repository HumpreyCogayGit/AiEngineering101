# EXER049 — Learning from Production

**Module 9 · Running in Production** · Lecture: [Lecture/lectures/lec049.html](../Lecture/lectures/lec049.html)

## Goal

Close the loop from production back to the evaluation set: find the answers customers were unhappy
with, choose what a person reviews, turn reviewed failures into evaluation cases, and notice when
quality or cost drifts between weeks.

## The project

| File | Status | Your work |
|---|---|---|
| `feedback_loop.py` | TODO | `implicit_signals`, `sample_for_review`, `to_eval_case`, `dedupe`, `weekly_metrics`, `drift_alerts` |
| `traces.jsonl` | given | four weeks of (synthetic) production traces of the helpdesk: 291 questions |
| `reviews.json` | given | a person's verdicts for the review queue |
| `make_traces.py` | given | how the traces were generated (deterministic) |

```
traces + feedback ─► signals ─► review queue ─► reviewed failures ─► new eval cases ─► EXER048 gate
                  └► weekly metrics ─► drift alerts
```

## Run it

```bash
uv run python EXER049/starter/feedback_loop.py     # offline: queue, new cases, weekly metrics, alerts
uv run python EXER049/check.py
```

## Success criteria

- [ ] A request for a person, or the same question again within a minute, marks the previous answer
- [ ] The review queue holds every thumbs-down and every signal, plus a reproducible random sample, and no blocked attacks
- [ ] A reviewed failure becomes a case in the EXER037 format that its `score_case` accepts; duplicates are dropped
- [ ] Weekly metrics show the thumbs-down rate, refusal rate, tokens and p95 latency per ISO week
- [ ] The drift in the last week (refusals and latency) raises alerts; the quiet weeks do not
- [ ] All 7 checks pass (offline)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Let a model pre-triage the review queue with the documents in view, and compare it with the person's verdicts. *Done when:* the script prints the agreement and, separately, the failures the model called "ok".
2. **Connect (EXER048).** Run the new candidate cases against today's assistant before they enter the gate. *Done when:* each case is reported as failing today (a live bug) or passing (a guard against a return).

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER049/stretch/goal1_llm_triage.py
uv run python EXER049/stretch/goal2_candidates_vs_today.py
```
