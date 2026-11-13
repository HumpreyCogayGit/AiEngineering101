# EXER007 — Streaming

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec007.html](../Lecture/lectures/lec007.html)

## Goal

Show the answer word by word as the model generates it, understand chunks and
deltas, and measure why streaming *feels* so much faster.

## Tasks

Complete the TODOs in `starter/streaming.py`:

1. `stream_reply` — a generator that yields each text delta
2. `collect` — consume a stream, print as you go, return the full text
3. `stream_with_usage` — also capture token usage from the final chunk

## Run it

```bash
uv run python EXER007/starter/streaming.py
uv run python EXER007/check.py
```

## Success criteria

- [ ] Answers appear progressively in the terminal, not all at once
- [ ] On exit the script prints time-to-first-token and total time; the first is much smaller
- [ ] Chunks without `choices` (the usage chunk, or Azure's content-filter chunk) don't crash your code
- [ ] All 5 checks pass
