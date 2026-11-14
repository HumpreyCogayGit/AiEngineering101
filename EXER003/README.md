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
| `build_url(base_url)` | Return `<base_url>/chat/completions` (no double slash) |
| `build_headers(api_key)` | Return the `Authorization: Bearer <key>` and `Content-Type` headers |
| `build_body(model, prompt)` | Return the JSON body with one user message |
| `send_chat(prompt, model=None)` | POST with `httpx`, raise on HTTP errors, return the JSON |

## Run it

```bash
uv run python EXER003/starter/raw_call.py
uv run python EXER003/check.py
```

## Success criteria

- [ ] The script prints the full JSON response, then the reply, finish reason and usage
- [ ] A model name that does not exist produces a readable `HTTP 4xx` message instead of a crash
- [ ] All 6 checks pass (2 of them call the live API)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Send the same question twice, with and without a system message, and compare `usage.prompt_tokens`. *Done when:* the script prints how many extra input tokens the system message costs.
2. **Connect (EXER011).** Print the rate-limit headers of the response. *Done when:* a hosted provider shows its `x-ratelimit-*` headers, and a local one prints that there are none.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER003/stretch/goal1_system_message.py
uv run python EXER003/stretch/goal2_rate_limit_headers.py
```
