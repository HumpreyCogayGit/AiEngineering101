# EXER037 — Capstone: Nimbus Helpdesk

**Module 7 · Toward Production** · Lecture: [Lecture/lectures/lec037.html](../Lecture/lectures/lec037.html)

## Goal

Combine everything from the course into one assistant that customers and staff
of Nimbus Coffee Co. can actually use — then prove it works with an evaluation.

## What you are building

```
           ┌────────────── interfaces ──────────────┐
           │  cli.py (Typer)       app.py (Streamlit)│
           └───────────────┬─────────────────────────┘
                           │  Assistant.ask(question, thread_id)
                ┌──────────▼──────────┐
                │  guards.check_input │  ← blocked? stop here
                │  LangGraph agent    │  ← create_agent + InMemorySaver (memory per thread)
                │   ├ search_knowledge_base  (RAG over data/knowledge_base, Chroma)
                │   ├ calculator             (exact math)
                │   └ notes_* tools          (MCP server, least privilege: no delete)
                │  guards.check_output│  ← unsafe? withhold
                └──────────┬──────────┘
                           │  Reply(answer, tools_used, blocked, reasons, tokens)
                    evaluate.py → output/capstone_eval.md
```

| File | Status | What to do |
|---|---|---|
| `guards.py` | given | input/output guardrails from EXER036 |
| `tools.py` | TODO | `search_knowledge_base` body, `load_mcp_tools` |
| `assistant.py` | TODO | `Assistant.setup`, `Assistant.ask` |
| `cli.py` | TODO | the `ask` command |
| `app.py` | TODO | answering in the chat UI |
| `evaluate.py` | TODO | `score_case` |

## Run it

```bash
uv run python EXER037/starter/cli.py ask "What is your refund policy?" -v
uv run python EXER037/starter/cli.py chat
uv run streamlit run EXER037/starter/app.py
uv run python EXER037/starter/cli.py eval
uv run python EXER037/check.py
```

## Success criteria

- [ ] All 11 checks pass, including the live evaluation (≥ 80% of [eval_set.json](eval_set.json))
- [ ] The CLI and the web UI give the same answers
- [ ] Conversations remember earlier turns within a thread
- [ ] Prompt-injection attempts are blocked before reaching the model
- [ ] You wrote a short review (below) of your own assistant

## Rubric (self-review or peer review)

| Area | 1 — needs work | 2 — solid | 3 — excellent |
|---|---|---|---|
| **Correctness** | eval < 80% | eval ≥ 80% | eval 100%, and you added 5+ cases of your own |
| **Grounding** | answers without sources | cites sources | refuses cleanly when documents don't cover it |
| **Tool use** | does math in its head | uses tools as designed | tool errors handled; least privilege documented |
| **Safety** | no guardrails | input + output guards | you red-teamed it and wrote down what still gets through |
| **Observability** | none | tokens shown per answer | you added the EXER035 tracker or LangSmith and checked the cost per question |
| **Code quality** | duplicated logic | logic separated from UI | tested, documented, easy to extend with a new tool |

## Write your review

Create `EXER037/REVIEW.md` answering:

1. Which eval cases failed first, and what change fixed them?
2. What is your average cost per question? How would you reduce it?
3. Name one attack that still gets through. How would you stop it?
4. What would you need to change to put this in front of real customers?

## Ideas for going further

- Add human-in-the-loop approval (EXER029) before any note is saved
- Stream answers token by token in the UI
- Swap `InMemorySaver` for SQLite (EXER028) so conversations survive restarts
- Add agentic retrieval (EXER030) or hybrid search (EXER023) inside `search_knowledge_base`
- Deploy the Streamlit app to Azure App Service or Azure Container Apps
