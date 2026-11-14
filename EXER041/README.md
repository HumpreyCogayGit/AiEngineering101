# EXER041 — Deploying the Capstone

**Module 8 · Beyond the Capstone** · Lecture: [Lecture/lectures/lec041.html](../Lecture/lectures/lec041.html)

## Goal

Turn the EXER037 helpdesk into a service that runs anywhere: an HTTP API in a
container image, configured only through environment variables, that reports
its own health.

## The project

| File | Status | Your work |
|---|---|---|
| `service.py` | TODO | `service_port`, `check_config`, `liveness`, `readiness`, `route` |
| `Dockerfile` | TODO | install locked dependencies, non-root user, port, health check, start command |
| `Dockerfile.dockerignore` | TODO | keep `.env`, `.venv/`, `.chroma/` and `.git/` out of the build |

The assistant is the EXER037 one, unchanged. `service.py` is a third thin shell around
`Assistant.ask`, next to the CLI and the Streamlit app. It serves the reference capstone by
default; set `HELPDESK_CODE=starter` to serve your own.

| Route | Answers |
|---|---|
| `GET /healthz` | `200 {"status": "ok"}` while the process runs (liveness) |
| `GET /readyz` | `200` when it can serve, `503` with the reasons when it cannot (readiness) |
| `POST /ask` | `{"question": "...", "thread_id": "optional"}` → the helpdesk's `Reply` as JSON |

## Run it

Without Docker. The service reads **real environment variables only**, so export your `.env` first:

```bash
set -a; source .env; set +a
uv run python EXER041/starter/service.py
curl localhost:8000/readyz
curl -X POST localhost:8000/ask -d '{"question": "Is shipping free?"}'
uv run python EXER041/check.py
```

With Docker, from the repository root:

```bash
docker build -f EXER041/starter/Dockerfile -t nimbus-helpdesk .
docker run --rm -p 8000:8000 --env-file .env nimbus-helpdesk
docker ps          # the STATUS column shows (healthy) after about 30 seconds
```

`--env-file` passes every line of `.env` as it is written: values must not be wrapped in quotes.
For Ollama on your own machine, the container reaches it at `OLLAMA_BASE_URL=http://host.docker.internal:11434`.

## Success criteria

- [ ] `uv run python EXER041/starter/service.py` refuses to start, naming the missing variables, when the environment is empty
- [ ] `/healthz` answers 200, and `/readyz` answers 503 with the reason when a check fails
- [ ] Two questions with the same `thread_id` share a conversation
- [ ] The image builds, the container answers a question, and `docker ps` shows it as `(healthy)`
- [ ] `docker run --rm nimbus-helpdesk ls -a /app` shows no `.env`, and `whoami` inside the container is not `root`
- [ ] All 12 checks pass (offline; they do not need Docker)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a readiness check for the vector index, and build the index in a warm-up thread at start. *Done when:* `/readyz` answers 503 until the index exists and 200 afterwards, while `/healthz` stays 200.
2. **Connect (EXER035).** Write one structured JSON log line per question, and add a `GET /stats` route with running totals. *Done when:* each question logs thread, seconds, tokens and tools (never the question text), and `/stats` returns the totals.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER041/stretch/goal1_index_readiness.py
uv run python EXER041/stretch/goal2_request_stats.py
```
