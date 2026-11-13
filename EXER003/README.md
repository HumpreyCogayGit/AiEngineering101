# EXER003 — HTTP and the Raw API Call

**Module 0 · Foundations** · Lecture: [Lecture/lectures/lec003.html](../Lecture/lectures/lec003.html)

## Goal

Make your first LLM call with nothing but HTTP, so you see exactly what every
SDK and framework does underneath: a URL, some headers, a JSON body, and a JSON
response.

## Tasks

Complete the TODOs in `starter/raw_call.py`:

| Function | What it must do |
|---|---|
| `build_url(endpoint)` | Return `<endpoint>/openai/v1/chat/completions` (no double slash) |
| `build_headers(api_key)` | Return the `api-key` and `Content-Type` headers |
| `build_body(deployment, prompt)` | Return the JSON body with one user message |
| `send_chat(prompt, api_key=None)` | POST with `httpx`, raise on HTTP errors, return the JSON |

## Run it

```bash
uv run python EXER003/starter/raw_call.py
uv run python EXER003/check.py
```

## Success criteria

- [ ] The script prints the full JSON response, then the reply, finish reason and usage
- [ ] A wrong key produces a readable `HTTP 401` message instead of a crash
- [ ] All 6 checks pass (2 of them call the live API)

## Stretch

- Try a deployment name that does not exist. What status code do you get?
- Add `"temperature": 0` to the body and run it a few times.
