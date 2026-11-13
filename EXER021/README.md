# EXER021 — Vector Store with Chroma

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec021.html](../Lecture/lectures/lec021.html)

## Goal

Store embedded chunks in a persistent **Chroma** vector database, search it
with scores and metadata filters, and make ingestion idempotent.

## Tasks

Complete the TODOs in `starter/vector_store.py`:

1. `make_id` — deterministic, content-based ids
2. `open_store` — a persistent Chroma collection using cosine distance
3. `add_chunks` — only add chunks that aren't stored yet
4. `search` — `similarity_search_with_score` with an optional `source` filter

## Run it

```bash
uv run python EXER021/starter/vector_store.py      # run it twice!
uv run python EXER021/check.py
```

The database is stored in `.chroma/` at the repository root (git-ignored).

## Success criteria

- [ ] First run adds all chunks; the second run adds 0
- [ ] "Can I bring my dog?" finds the pets paragraph in `company_faq.md`
- [ ] The `source` filter limits results to one file
- [ ] All 6 checks pass

From EXER022 on, `aicourse.rag.get_vector_store()` does all of this for you.
