# EXER022 — The RAG Chain

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec022.html](../Lecture/lectures/lec022.html)

## Goal

Connect retrieval and generation into a complete RAG pipeline that answers
from your documents, cites its sources, and admits when it doesn't know.

## Tasks

Complete the TODOs in `starter/rag_chain.py`:

1. `RAG_PROMPT` — a grounding prompt with citation and "I don't know" rules
2. `format_docs` — numbered passages with their sources
3. `build_rag_chain` — retriever + prompt + model, returning answer **and** docs
4. `cited_sources` — turn `[n]` markers back into file names

## Run it

```bash
uv run python EXER022/starter/rag_chain.py
uv run python EXER022/check.py
```

The first run builds the Chroma index (a few seconds).

## Success criteria

- [ ] Policy questions are answered correctly with `[n]` citations
- [ ] Sources are printed under each answer
- [ ] "What is the capital of Peru?" gets the exact "I don't know" reply
- [ ] All 7 checks pass
