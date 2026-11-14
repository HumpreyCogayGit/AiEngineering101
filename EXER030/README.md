# EXER030 — Agentic RAG

**Module 5 · Agents with LangGraph** · Lecture: [Lecture/lectures/lec030.html](../Lecture/lectures/lec030.html)

## Goal

Turn fixed RAG into a graph that decides: whether to retrieve, which chunks
are relevant, when to rewrite the query and retry, and when to give up.

```
START → route ─┬→ direct_answer → END
               └→ retrieve → grade ─┬→ generate → END
                     ↑               ├→ rewrite ─┘(retry)
                     └───────────────┘
                                     └→ fallback → END
```

## Tasks

Complete the TODOs in `starter/agentic_rag.py`: `decide`, `grade`,
`after_grade`, and the graph edges.

## Run it

```bash
uv run python EXER030/starter/agentic_rag.py
uv run python EXER030/check.py
```

## Success criteria

- [ ] "Hi there!" skips retrieval
- [ ] "something about beans going back" gets an answer with a citation (directly, or after
      a rewrite when the first search finds nothing relevant: the path tells you which)
- [ ] "What is the GDP of France?" is sent to retrieval, not answered from the model's own
      knowledge, and ends in the honest fallback after 2 rewrites
- [ ] The printed `path` explains every decision
- [ ] All 5 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a hallucination check on the generated answer before it is returned. *Done when:* an answer with an invented fact is replaced by the fallback, and the path ends in `verify -> fallback`.
2. **Connect (EXER024).** Score the graph on the EXER024 evaluation set against the plain chain. *Done when:* one table shows the five metrics and the model calls per question for both.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER030/stretch/goal1_hallucination_check.py
uv run python EXER030/stretch/goal2_score_against_chain.py
```
