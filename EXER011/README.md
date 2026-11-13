# EXER011 — Reliability

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec011.html](../Lecture/lectures/lec011.html)

## Goal

Make LLM calls production-ready: retry temporary failures with exponential
backoff and jitter, fail fast on permanent ones, log what happens, and run many
calls concurrently with a limit.

## Tasks

Complete the TODOs in `starter/reliable.py`:

1. `backoff_delay` — exponential growth, a cap, and jitter
2. `call_with_retry` — retry only the errors in `RETRYABLE`
3. `complete_many` — `asyncio.Semaphore` + `asyncio.gather`

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
