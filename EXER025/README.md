# EXER025 — Chat With Your Docs

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec025.html](../Lecture/lectures/lec025.html)

## Goal

Ship a complete RAG product: a Streamlit app where users upload their own
files, ask follow-up questions in a conversation, and see the sources behind
every answer.

## Tasks

1. `starter/docs_logic.py` — `load_uploaded`, `build_index` (in-memory, per session),
   `condense_question` (rewrite follow-ups), `answer`
2. `starter/app.py` — build the index from uploads, show sources in an expander

## Run it

```bash
uv run streamlit run EXER025/starter/app.py
uv run python EXER025/check.py
```

## Success criteria

- [ ] Uploading a PDF or Markdown file and clicking "Build index" works
- [ ] Follow-ups work: "Tell me about the cold brew bottle" → "How much is it?"
- [ ] Every answer has a Sources expander with file names (and PDF page numbers)
- [ ] Two browser tabs do not see each other's documents
- [ ] All 7 checks pass
