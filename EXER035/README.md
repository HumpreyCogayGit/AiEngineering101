# EXER035 — Observability and Cost

**Module 7 · Toward Production** · Lecture: [Lecture/lectures/lec035.html](../Lecture/lectures/lec035.html)

## Goal

See inside your agents: build a callback handler that records every model
call and tool call as a span with latency, tokens, cost and errors, then print
a timeline and a usage report.

## Tasks

Complete the TODOs in `starter/observability.py` (the `UsageTracker`):

1. `on_llm_end` — close the span, record tokens and what the model decided
2. `on_tool_start`, `on_tool_end`, `on_tool_error`
3. `report` — totals and cost

## Run it

```bash
uv run python EXER035/starter/observability.py
uv run python EXER035/check.py
```

## Optional: LangSmith

LangSmith is LangChain's hosted tracing tool. Create a free account at
smith.langchain.com, then add to `.env`:

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=ai-engineer-course
```

Run any exercise again and open the trace in the LangSmith UI. Compare it
with your own timeline.

## Success criteria

- [ ] The timeline shows each model call (with tokens and its decision) and each tool call
- [ ] The failing inventory tool appears with ❌ and its error
- [ ] The report gives the total cost of the run in USD
- [ ] All 5 checks pass (offline)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add latency percentiles (p50, p95) per tool to the report. *Done when:* the report shows a tool whose p50 is better and whose p95 is worse than another's.
2. **Connect (EXER015).** Export the spans as JSON and draw the timeline in Streamlit. *Done when:* `stretch/output/trace.json` is written, and the app shows one bar per span from its start to its end.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER035/stretch/goal1_latency_percentiles.py
uv run python EXER035/stretch/goal2_export_spans.py
```

Also in [stretch/](stretch/): `goal2_timeline_app.py`.
