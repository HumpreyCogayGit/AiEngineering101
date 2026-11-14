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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Delete and re-ingest one changed document without touching the others. *Done when:* after an edit to one file, only its stale chunks are deleted and only its new chunks are added.
2. **Connect (EXER019).** Store the same chunks in a cosine collection and an L2 collection, and compare the results of the same queries. *Done when:* the script prints both rankings and says whether your embedding vectors have unit length.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER021/stretch/goal1_reingest_one.py
uv run python EXER021/stretch/goal2_cosine_vs_l2.py
```
