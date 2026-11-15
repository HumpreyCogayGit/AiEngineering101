# EXER046 — Model Selection and Routing

**Module 9 · Running in Production** · Lecture: [Lecture/lectures/lec046.html](../Lecture/lectures/lec046.html)

## Goal

Choose a model with measurements instead of reputation, send each question to the cheapest model that
can answer it, fall back when the provider fails, and know before a model is retired.

## The project

| File | Status | Your work |
|---|---|---|
| `routing.py` | TODO | `summarize`, `choose`, `route_question`, `needs_escalation`, `with_provider_fallback`, `retiring_soon` |
| `models.json` | given | prices and retirement dates (example values: fill in your provider's) |

Given: the task suite (8 ticket classifications from EXER008, 4 structured extractions, 4 tool choices),
`run_case`, and `RoutedHelpdesk`, which uses your router around two EXER037 assistants.

Candidates are chat models on your provider, set in `AICOURSE_COMPARE_MODELS`:

```bash
AICOURSE_COMPARE_MODELS="gemma4:e4b,qwen2.5:3b"                 # Ollama: two local models
AICOURSE_COMPARE_MODELS="my-deployment@low,my-deployment@high"  # one model at two reasoning efforts
```

Without it, the only candidate is your configured chat model.

## Run it

```bash
uv run python EXER046/starter/routing.py compare     # the suite on every candidate, and the choice (live)
uv run python EXER046/starter/routing.py route       # first candidate = small, last = large (live)
uv run python EXER046/check.py
```

## Success criteria

- [ ] The comparison prints accuracy per task, p50/p95 latency, errors and cost per 1,000 requests for every candidate
- [ ] `choose` picks the cheapest candidate that meets every bar, prefers a known price, and returns None when none qualifies
- [ ] Easy questions go to the small model, arithmetic, reasons, complaints and long questions to the large one
- [ ] A small model's answer is escalated when it searched and still could not answer, never for a correct off-topic refusal
- [ ] Provider errors fall back to another model; a bug in the request is not hidden
- [ ] Models retiring within 90 days are reported, soonest first
- [ ] All 9 checks pass (one is `[live API]`: it runs the suite on your model)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Run the suite several times per candidate and decide whether their difference is larger than the noise. *Done when:* the script prints each task's accuracy per run, its spread, and a verdict per task.
2. **Connect (EXER038).** Score the capstone's multi-step tool trajectories on every candidate with the EXER038 scorer. *Done when:* the script prints each trajectory, what is missing, and a total per candidate.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER046/stretch/goal1_noise_vs_difference.py
uv run python EXER046/stretch/goal2_trajectories_per_model.py
```
