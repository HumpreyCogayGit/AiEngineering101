# EXER011 — Reliability

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec011.html](../Lecture/lectures/lec011.html)

## Goal

Make LLM calls production-ready: retry temporary failures with exponential
backoff and jitter, fail fast on permanent ones, log what happens, and run many
calls concurrently with a limit.

## Tasks

Complete the TODOs in `starter/reliable.py`:

1. `backoff_delay`: exponential growth, a cap, and jitter
2. `call_with_retry`: retry only the errors in `RETRYABLE`
3. `complete_many`: `asyncio.Semaphore` + `asyncio.gather`

## Run it

```bash
uv run python EXER011/starter/reliable.py
uv run python EXER011/check.py
```

## Success criteria

- [ ] The retry demo logs two warnings, then succeeds
- [ ] 6 prompts run concurrently (at most 3 in flight), noticeably faster than one after
      another, with results in input order
- [ ] A `ValueError` is not retried; a `RateLimitError` is
- [ ] All 5 checks pass (they run offline and instantly)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a circuit breaker: after N consecutive failures, stop calling for a while and fail at once. *Done when:* during a simulated outage the later requests send nothing, and the first request after the cool-down closes the circuit again.
2. **Connect (EXER008).** Run the EXER008 evaluation concurrently, with a limit, and report the speed-up. *Done when:* both runs give the same accuracy and the script prints the speed-up factor.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER011/stretch/goal1_circuit_breaker.py
uv run python EXER011/stretch/goal2_concurrent_eval.py
```

## Transfer task (end of Module 1)

Optional, and different from the stretch goals: a new problem in a new domain, with **no starter code and no `check.py`**. It shows whether you can use Module 1's ideas without scaffolding.

Build an **IT ticket triager** for a different company, with no starter code. For each ticket in
[transfer/tickets.json](transfer/tickets.json), return its system (network, email, payroll, hardware,
security), a severity (low to critical) and whether an engineer must act. The labels are in the same file.

- [ ] The result of every call is a validated Pydantic object, not text you parse yourself (EXER009)
- [ ] The prompt defines every category and severity, and shows at least two examples (EXER008)
- [ ] Calls are retried with backoff on temporary errors, and run concurrently with a limit (EXER011)
- [ ] The script prints accuracy per field over all 12 tickets
- [ ] You can explain the misses of the weakest field, and whether the label or the prompt is wrong

Reference answer, for after you have tried:

```bash
uv run python EXER011/transfer/reference_triage.py
```
