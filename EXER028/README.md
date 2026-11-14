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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Summarize old turns into one message when the thread grows long, and remove them from the state. *Done when:* the thread never holds more than a few messages, and the bot still knows a fact from the first turn.
2. **Connect (EXER010).** Write a small CLI that lists and deletes a user's long-term memories. *Done when:* `list` shows the stored facts with ids, and after `delete` or `forget` they are gone in a new process too.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER028/stretch/goal1_summarize_old_turns.py
uv run python EXER028/stretch/goal2_memory_cli.py list bea
```
