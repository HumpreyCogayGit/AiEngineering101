# EXER022 — The RAG Chain

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec022.html](../Lecture/lectures/lec022.html)

## Goal

Connect retrieval and generation into a complete RAG pipeline that answers
from your documents, cites its sources, and admits when it doesn't know.

## Tasks

Complete the TODOs in `starter/rag_chain.py`:

1. `RAG_PROMPT`: a grounding prompt with citation and "I don't know" rules
2. `format_docs`: numbered passages with their sources
3. `build_rag_chain`: retriever + prompt + model, returning answer **and** docs
4. `cited_sources`: turn `[n]` markers back into file names

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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Return the exact quoted sentence that supports each citation, and verify the quote in code. *Done when:* every citation prints its quote and `verified`, and the out-of-scope question has no citations.
2. **Connect (EXER007).** Stream the answer token by token and print the sources at the end. *Done when:* the answer appears progressively, followed by its sources and the time to first token.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER022/stretch/goal1_quoted_citations.py
uv run python EXER022/stretch/goal2_stream_with_sources.py
```
