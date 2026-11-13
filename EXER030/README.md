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
