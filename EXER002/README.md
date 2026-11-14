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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Support the `tool` role, whose message must carry a `tool_call_id`. *Done when:* a tool message with an id parses, and one without it raises a `ValidationError` that names `tool_call_id`.
2. **Connect (EXER003).** Describe the whole response in `sample_response.json` with nested Pydantic models, and validate the file with them. *Done when:* `response.choices[0].message.content` and `response.usage.total_tokens` work as attributes, and a malformed response lists every missing field.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER002/stretch/goal1_tool_role.py
uv run python EXER002/stretch/goal2_response_model.py
```
