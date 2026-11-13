# EXER009 — Response Formatting

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec009.html](../Lecture/lectures/lec009.html)

## Goal

Get **data** out of a model instead of prose: JSON mode, schema-enforced
structured outputs with Pydantic, and a validate-and-repair loop for when you
need a fallback.

## The project

An event extractor: turn a messy email into an `Event` object with title, date,
time, location and attendees.

## Tasks

Complete the TODOs in `starter/formatting.py`:

1. `extract_json_mode` — `response_format={"type": "json_object"}`
2. `extract_structured` — `client.chat.completions.parse(response_format=Event)`
3. `parse_with_repair` — validate with Pydantic and feed errors back to the model

## Run it

```bash
uv run python EXER009/starter/formatting.py
uv run python EXER009/check.py
```

## Success criteria

- [ ] All three methods extract the date as `2026-03-14`
- [ ] `extract_structured` returns a real `Event` object, not a dict or string
- [ ] The repair loop recovers from a reply that is missing fields, and gives up after `max_attempts`
- [ ] All 6 checks pass
