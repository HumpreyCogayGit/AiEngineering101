# EXER017 — Tools in LangChain

**Module 3 · Tool Calling** · Lecture: [Lecture/lectures/lec017.html](../Lecture/lectures/lec017.html)

## Goal

Define tools with `@tool`, bind them with `bind_tools`, run the loop with
LangChain messages, then replace the loop with the prebuilt `create_agent`.

## Tasks

Complete the TODOs in `starter/lc_tools.py`:

1. `convert_currency` and `word_count` as `@tool` functions
2. `run_tool_loop` — the EXER016 loop using `AIMessage.tool_calls` and `ToolMessage`,
   answering every call when the model requests several at once (parallel tool calls)
3. `build_agent` — `create_agent(llm, TOOLS, system_prompt=...)`

## Run it

```bash
uv run python EXER017/starter/lc_tools.py
uv run python EXER017/check.py
```

## Success criteria

- [ ] The script prints the auto-generated schema of `convert_currency`
- [ ] One question triggers both `convert_currency` and `get_weather`, and the trace
      shows one `ToolMessage` per tool call
- [ ] Your loop and `create_agent` give equivalent answers
- [ ] All 7 checks pass
