# EXER023 — Better Retrieval

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec023.html](../Lecture/lectures/lec023.html)

## Goal

Improve retrieval quality with keyword + vector hybrid search, rank fusion,
MMR, multi-query rewriting and LLM reranking, and **measure** each one with
hit rate instead of trusting intuition.

## Tasks

Complete the TODOs in `starter/better_retrieval.py`:

1. `BM25Retriever`: keyword search with `rank_bm25`
2. `reciprocal_rank_fusion`: merge several rankings
3. `multi_query`: ask the model for alternative phrasings
4. `hit_rate`: the metric that decides what works

(`llm_rerank` is provided. Read it.)

## Run it

```bash
uv run python EXER023/starter/better_retrieval.py
uv run python EXER023/check.py
```

## Success criteria

- [ ] A hit-rate table for six retrieval strategies is printed, at @1 and @4
- [ ] BM25 finds exact rare words such as "Liberica"
- [ ] Hybrid retrieval scores at least as well as plain vector search, and at least 80%
- [ ] You can explain the cost (latency, tokens) of multi-query and reranking
- [ ] All 7 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add MRR as a second metric beside hit rate. *Done when:* the table has an MRR column, and two strategies with the same hit rate @4 differ in it.
2. **Connect (EXER024).** Add five harder questions that separate the strategies at @4. Keep them in your own file: other checks rely on `data/eval_questions.json`. *Done when:* at least two strategies score differently at @4 on your questions, and you can say why each question is hard.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER023/stretch/goal1_mrr.py
uv run python EXER023/stretch/goal2_harder_questions.py
```

Also in [stretch/](stretch/): `hard_questions.json`.
