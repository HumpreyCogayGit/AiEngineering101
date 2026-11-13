# EXER012 — LangChain Chat Models

**Module 2 · LangChain** · Lecture: [Lecture/lectures/lec012.html](../Lecture/lectures/lec012.html)

## Goal

Rebuild what you made in Module 1 with LangChain, and see what the framework
gives you: typed messages, one interface for every provider, and `invoke`,
`stream` and `batch` on every model.

## Tasks

Complete the TODOs in `starter/lc_chat.py`:

1. `make_llm` — build `ChatOpenAI` by hand from settings
2. `ask` — `SystemMessage` + `HumanMessage`, then `invoke`
3. `batch_ask`, `stream_print`
4. `LCConversation.send` — the EXER005 chatbot with message objects

## Run it

```bash
uv run python EXER012/starter/lc_chat.py
uv run python EXER012/check.py
```

## Success criteria

- [ ] The script answers, shows `usage_metadata`, batches 3 questions, streams, and remembers a colour
- [ ] You can explain which Module 1 code each LangChain call replaces
- [ ] You read answers with `.text` (always a string), not `.content` (a string or a list of blocks)
- [ ] All 8 checks pass

From now on exercises use `aicourse.llm.get_chat_model()`, which is your `make_llm()`.
