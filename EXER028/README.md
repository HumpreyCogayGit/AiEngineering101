# EXER028 — Memory and Persistence

**Module 5 · Agents with LangGraph** · Lecture: [Lecture/lectures/lec028.html](../Lecture/lectures/lec028.html)

## Goal

Give an agent memory: short-term memory per conversation thread with
checkpointers (in-memory and SQLite), and long-term memory per user with a
Store, plus trimming so long conversations still fit the context window.

## Tasks

Complete the TODOs in `starter/memory_bot.py`:

1. `recall` — read a user's facts from the store
2. the `chat` node — inject facts into the system prompt, trim history
3. the `save_memories` node — extract and store new facts
4. compile with a checkpointer and a store
5. `sqlite_checkpointer`

## Run it

```bash
uv run python EXER028/starter/memory_bot.py      # run it twice
uv run python EXER028/check.py
```

## Success criteria

- [ ] Thread A remembers "Bea"; thread C (another user) does not
- [ ] Thread B (same user, new thread) avoids dairy — long-term memory works
- [ ] Re-running the script restores thread A from SQLite
- [ ] All 6 checks pass (offline)
