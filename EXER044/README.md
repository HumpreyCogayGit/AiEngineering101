# EXER044 — Operating Under Load

**Module 9 · Running in Production** · Lecture: [Lecture/lectures/lec044.html](../Lecture/lectures/lec044.html)

## Goal

Put limits in front of the helpdesk so it says no early and clearly when it is busy, stops cleanly when
the platform stops it, and measure what users experience with a local load test.

## The project

| File | Status | Your work |
|---|---|---|
| `load_service.py` | TODO | `TokenBucket.take`, `AdmissionControl.acquire`, `install_sigterm_handler`, `route` |
| `loadtest.py` | TODO | `percentile`, `summarize`, `slo_report` |
| `Dockerfile` | given | the EXER042 service with limits, as an image |

The service builds on EXER042: authentication and per-user namespaces are imported from its reference
solution. `TokenBudget`, `GracefulShutdown` and the HTTP plumbing are given.

| Situation | Answer |
|---|---|
| Body larger than 20 KB | `413`, without reading the body |
| User over their rate (a burst of 5, then 20 a minute) | `429` + `Retry-After` |
| User over their daily token budget | `429` + `Retry-After` (seconds to midnight UTC) |
| Every slot busy and the queue full, or waited too long | `503` + `Retry-After` |
| No answer within the deadline | `504` |
| Shutting down | `503` for new questions; running ones finish; then exit 0 |

## Run it

```bash
uv run python EXER044/starter/loadtest.py                  # offline: a fake assistant, two concurrency limits
HELPDESK_FAKE_SECONDS=0.5 uv run python EXER044/starter/load_service.py   # needs tokens from EXER042's `issue`
uv run python EXER044/check.py

docker build -f EXER044/starter/Dockerfile -t nimbus-helpdesk-load .
docker run -d --name helpdesk -p 8000:8000 --env-file .env nimbus-helpdesk-load
time docker stop helpdesk                                  # under a second; EXER041's image waits and is killed
```

## Success criteria

- [ ] Every refusal (413, 429, 503) happens before any model call, and 429 and 503 carry `Retry-After`
- [ ] A question that misses the deadline gets 504, and keeps its slot until its work actually stops
- [ ] On SIGTERM the process finishes the question in flight, answers new ones with 503, and exits 0
- [ ] The load test prints throughput, p50/p95/p99, counts by status, and whether the SLO was met
- [ ] All 9 checks pass (offline; one starts the service as a real process and sends it SIGTERM)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Sweep the concurrency limit against a simulated provider that serves 4 requests at once, and find the knee. *Done when:* a table shows throughput and p95 per limit, and the script names the largest limit that meets the p95 objective.
2. **Connect (EXER011).** Write a client that honours `Retry-After` with jitter, and compare it with one that retries at once. *Done when:* both send the same questions to the same service and the script prints answers, requests sent and refusals for each.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER044/stretch/goal1_find_the_knee.py
uv run python EXER044/stretch/goal2_retry_after_client.py
```
