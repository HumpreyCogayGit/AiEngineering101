# EXER037 — Capstone: Nimbus Helpdesk

**Module 7 · Toward Production** · Lecture: [Lecture/lectures/lec037.html](../Lecture/lectures/lec037.html)

## Goal

Combine everything from the course into one assistant that customers and staff
of Nimbus Coffee Co. could use, then measure it with an evaluation.

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
      evaluate.py + eval_set.json → output/capstone_eval.md (a score per category)
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
uv run python EXER037/starter/cli.py eval              # the development set: iterate on this
uv run python EXER037/starter/cli.py eval --heldout    # the held-out set: run it once, at the end
uv run python EXER037/check.py
```

## Success criteria

- [ ] All 14 checks pass, including the live evaluation: every category of [eval_set.json](eval_set.json) at ≥ 75%, and safety at 100%
- [ ] The CLI and the web UI give the same answers
- [ ] Conversations remember earlier turns within a thread
- [ ] Prompt-injection attempts are blocked before reaching the model
- [ ] You wrote a short review (below) of your own assistant

## The evaluation set

[eval_set.json](eval_set.json) has 26 cases in six categories: grounding, arithmetic, refusal, memory
(the case's `history` is asked first, in the same thread), tool use and safety. The bar is **per
category**: 75% in each, and 100% for safety. With four cases in a category, one failure is already
25 points, so an overall average would hide a category that fails completely.

A case can set `"expect_tools_in_order": true`: the price must be looked up before the calculator adds
it up. Lecture 038 scores whole tool-call trajectories (missing, extra and out-of-order calls).

[eval_heldout.json](eval_heldout.json) has one more case per category that you never tune on. Iterate
on the development set until it meets the bar, then run `eval --heldout` once. If the held-out set
fails where the development set passed, you fitted the cases, not the problem.

## Rubric (self-review or peer review)

| Area | 1: needs work | 2: solid | 3: excellent |
|---|---|---|---|
| **Correctness** | a category below its bar | every category meets its bar | the held-out set also meets the bar, and you added 5+ cases of your own |
| **Grounding** | answers without sources | cites sources | refuses cleanly when documents don't cover it |
| **Tool use** | does math in its head | uses tools as designed | tool errors handled; least privilege documented |
| **Safety** | no guardrails | input + output guards | you red-teamed it and wrote down what still gets through |
| **Observability** | none | tokens shown per answer | you added the EXER035 tracker or LangSmith and checked the cost per question |
| **Code quality** | duplicated logic | logic separated from UI | tested, documented, easy to extend with a new tool |

## Write your review

Create `EXER037/REVIEW.md` answering:

1. Which categories failed first, and what change fixed them? Did the held-out set agree?
2. What is your average cost per question? How would you reduce it?
3. Name one attack that still gets through. How would you stop it?
4. What would you need to change to put this in front of real customers?

## Ideas for going further

- Add human-in-the-loop approval (EXER029) before any note is saved
- Stream answers token by token in the UI
- Swap `InMemorySaver` for SQLite (EXER028) so conversations survive restarts
- Add agentic retrieval (EXER030) or hybrid search (EXER023) inside `search_knowledge_base`
- Deploy the Streamlit app to Azure App Service or Azure Container Apps

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add one new tool and two evaluation cases that need it. *Done when:* the two new cases pass only when the tool is used, and the original cases still pass.
2. **Connect (EXER035).** Attach the EXER035 tracker to the evaluation run and report its cost. *Done when:* the script prints model calls, tokens and cost for the run and per question.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER037/stretch/goal1_new_tool.py
uv run python EXER037/stretch/goal2_eval_cost.py
```

Also in [stretch/](stretch/): `extra_eval_cases.json`.
