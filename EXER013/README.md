# EXER013 — Prompts and Chains

**Module 2 · LangChain** · Lecture: [Lecture/lectures/lec013.html](../Lecture/lectures/lec013.html)

## Goal

Learn prompt templates, output parsers and the LCEL pipe syntax (`|`), and
compose a two-step chain where the second step uses the first step's output.

## The project

A news pipeline: **summarize** an article, then **translate** the summary.

## Tasks

Complete the TODOs in `starter/chains.py`:

1. `summary_prompt`, `translate_prompt` — `ChatPromptTemplate.from_messages`
2. `build_summary_chain`, `build_translate_chain` — `prompt | llm | StrOutputParser()`
3. `build_pipeline` — chain both with `RunnablePassthrough.assign`

## Run it

```bash
uv run python EXER013/starter/chains.py
uv run python EXER013/check.py
```

## Success criteria

- [ ] The script shows the template variables, a summary, a translation and a 3-language batch
- [ ] The pipeline output contains the original inputs plus `summary` and `translation`
- [ ] All 5 checks pass
