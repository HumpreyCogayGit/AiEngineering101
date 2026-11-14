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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a nested model: an `Address` (building, floor, room, city) inside the event. *Done when:* `event.address.city` and `event.address.floor` are attributes of a real object.
2. **Connect (EXER008).** Count how often the repair loop is needed over 20 runs, for a precise prompt and for a vague one. *Done when:* the script prints, per prompt, how many runs needed more than one model call.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER009/stretch/goal1_nested_model.py
uv run python EXER009/stretch/goal2_count_repairs.py
```
