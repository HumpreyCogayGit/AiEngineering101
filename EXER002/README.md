# EXER002 — Python Primer for AI Engineers

**Module 0 · Foundations** · Lecture: [Lecture/lectures/lec002.html](../Lecture/lectures/lec002.html)

## Goal

Become comfortable with the Python you need for every later exercise: dicts and
lists (JSON), functions with type hints, exceptions, and Pydantic models.

## Tasks

1. Open [sample_response.json](sample_response.json). This is a real-shaped answer from a chat model.
2. Complete every `TODO` in `starter/primer.py`:
   - `load_response`, `get_reply_text`, `get_total_tokens` — read nested JSON
   - `safe_get_reply` — handle malformed data with `try/except`
   - `build_request` — build the JSON body you will send in EXER003
   - `Message` + `parse_messages` — validate data with Pydantic

## Run it

```bash
uv run python EXER002/starter/primer.py
uv run python EXER002/check.py
```

This exercise needs no API key — everything runs offline.

## Success criteria

- [ ] `primer.py` prints the reply text, the token count and a request body
- [ ] `safe_get_reply` returns `None` for `{}`, `{"choices": []}` and a `None` message
- [ ] A message with `role: "robot"` is rejected by Pydantic
- [ ] All 8 checks pass
