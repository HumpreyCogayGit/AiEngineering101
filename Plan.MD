# AI Engineer Course: Zero to Hero — Project Plan

## 1. Overview

A hands-on course that takes a learner from their first LLM API call to building production-style agents. Every topic is taught through one lecture page and one exercise the learner builds and runs.

| Decision | Choice |
|---|---|
| Target learner | Little Python experience, new to deep-diving LLMs |
| Inference provider | Azure Foundry (chat + embedding deployments) or Ollama (local chat + embedding models), selected with `AICOURSE_PROVIDER` |
| Frameworks | LangChain, LangGraph |
| Web UI | Streamlit |
| Vector store | Chroma (local, persisted to disk) |
| Python tooling | uv + one root `pyproject.toml` |
| Lecture site | Plain HTML/CSS/JS in `Lecture/`, no build step |
| Configuration | Root level only; exercises never hold their own keys or dependencies |

**Teaching principles**

1. **Raw first, framework second.** Each concept is first done by hand (HTTP or the plain SDK), then with LangChain/LangGraph, so the learner knows what the framework hides.
2. **One new concept per exercise.** Each exercise builds on the previous ones and says which.
3. **Every exercise is runnable and checkable.** Success criteria are concrete, and most are verified by a test script.
4. **Explain the why.** Lectures cover the concept, the trade-offs and the common mistakes, not only the steps.

## 2. Repository Layout

```
AiEngineerCourse/
├── Plan.MD
├── README.md                 # Course intro, setup, how to run an exercise
├── pyproject.toml            # All dependencies for all exercises
├── uv.lock
├── .python-version           # Pinned Python version (managed by uv)
├── .env.example              # Template of required settings (committed)
├── .env                      # Real keys (git-ignored)
├── .gitignore
├── check_all.py              # Runs every exercise check: solutions pass, starters fail; validates the quizzes
├── check_quizzes.py          # Validates Lecture/assets/js/quizzes.js
├── aicourse/                 # Small shared package, installed in editable mode
│   ├── settings.py           # Loads and validates .env (pydantic-settings)
│   ├── llm.py                # get_chat_model(), get_embeddings() helpers
│   ├── check.py              # Helpers used by exercise checks
│   └── stretch.py            # Lets stretch-goal code import a reference solution
├── data/                     # Shared sample documents for the RAG exercises
├── EXER001/
├── EXER002/
├── ...
└── Lecture/
```

### Root configuration

- `.env.example` lists every setting with a comment: the provider switch, then one block per provider (Azure Foundry: endpoint, API key, chat and embedding deployment names; Ollama: base URL, chat and embedding model names).
- `aicourse/settings.py` is the single place that reads `.env`. It fails with a clear message naming the missing setting.
- Early exercises (Module 0 and 1) read the settings but build the HTTP request or SDK client by hand. `aicourse/llm.py` helpers are only used after the learner has built the same thing manually.
- The machine has Python 3.14; the project pins an older version (3.12 planned) through `.python-version` for library compatibility. The exact pin and library versions are confirmed when scaffolding.

### Exercise folder

```
EXER00N/
├── README.md        # Short brief: goal, tasks, how to run, success criteria, stretch goals, link to lecture
├── starter/         # Code with TODOs for the learner to complete
├── solution/        # Reference solution
├── stretch/         # Reference code for the two optional stretch goals (imports solution/, never changes it)
└── check.py         # Verifies the success criteria (uv run python EXER00N/check.py)
```

- Run commands always start from the repository root, for example `uv run python EXER005/starter/main.py` or `uv run streamlit run EXER014/starter/app.py`.
- Exercises that cannot be checked automatically (UI, open-ended prompts) have a manual checklist in the README instead of `check.py`.

## 3. Lecture Site (`Lecture/`)

Plain static site that opens directly from the file system or through `python -m http.server`.

```
Lecture/
├── index.html            # Course home: roadmap, modules, progress
├── setup.html            # Provider (Azure Foundry or Ollama) and local setup guide
├── glossary.html
├── lectures/
│   ├── lec001.html       # One page per exercise, same number as EXER001
│   └── ...
└── assets/
    ├── css/style.css
    ├── js/course.js      # Course manifest: modules, lecture titles, order
    ├── js/quizzes.js     # Self-check quiz questions, as data
    ├── js/app.js         # Sidebar, previous/next, progress, quizzes, theme, copy buttons
    ├── vendor/           # Local copies of highlight.js and Mermaid
    └── img/
```

**Every lecture page has the same sections:**

1. **Overview** — what this lesson is and where it sits in the course
2. **Concept** — the explanation, with diagrams and small code samples
3. **The Project** — what the learner builds in the exercise
4. **Goal** — the learning objectives
5. **Success Criteria** — the checklist that defines "done"
6. **Walkthrough** — key steps and hints, without giving the solution away
7. **Common Pitfalls** — typical errors and how to recognize them
8. **Discussion** — questions and trade-offs worth thinking about
9. **Check Yourself** — a self-check quiz: 4 questions (5 for the longer lectures), multiple choice, with a one-sentence explanation for every option
10. **Further Reading** — official documentation links

The Walkthrough ends with the exercise's two **stretch goals**. Lectures 016–031 end their Concept section with a **worked example** built from captured output of a real run.

**Site features**

- Sidebar navigation and previous/next links generated from `course.js`, so adding a lecture means adding one entry and one HTML file.
- Syntax highlighting, copy button on code blocks, Mermaid diagrams for flows (message loop, RAG pipeline, agent graph).
- Light and dark theme, readable on mobile.
- "Mark as complete" per lecture, stored in the browser, with a progress bar on the home page.
- Quizzes are rendered by `app.js` from `quizzes.js`, so fixing a question never touches a lecture page. The score of the last attempt is stored in the browser and shown beside each lecture on the home page. It never blocks "Mark as complete".
- Libraries are stored in `assets/vendor/` so the site works offline and from `file://`.

## 4. Curriculum

41 exercises in 9 modules. Lecture `lecNNN.html` pairs with `EXERNNN`.

### Module 0 — Foundations

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 001 | Setup and First Check | Working environment; a script that confirms the settings load | uv, virtual environments, `.env`, secrets hygiene, inference providers (Azure Foundry deployments, Ollama models) |
| 002 | Python Primer for AI Engineers | Small scripts that parse and build nested JSON | dicts, lists, functions, type hints, JSON, Pydantic models, exceptions |
| 003 | HTTP and the Raw API Call | A chat completion sent with `httpx`, no SDK | REST, headers, auth, request and response bodies, status codes |

### Module 1 — Talking to an LLM

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 004 | The SDK and Model Parameters | The same call through the SDK, with a parameter experiment | client setup, temperature, max tokens, tokens, usage and cost, classic vs reasoning model parameters |
| 005 | Messages and Roles | A terminal chatbot that remembers the conversation | system/user/assistant roles, statelessness, history management |
| 006 | Message Content Blocks | A script that sends text plus an image | content parts, multimodal input, context window, trimming history |
| 007 | Streaming | A chatbot that prints tokens as they arrive | server-sent events, chunks and deltas, assembling the final message |
| 008 | Prompt Engineering Basics | A prompt library with measured before/after results | clear instructions, few-shot examples, delimiters, templates |
| 009 | Response Formatting | An extractor that returns validated data | JSON mode, JSON schema structured output, Pydantic validation, repair on failure |
| 010 | Building a CLI App | A proper command-line tool (`ask`, `chat`, `summarize <file>`) | Typer, arguments and options, stdin piping, exit codes |
| 011 | Reliability | A hardened client wrapper | errors, rate limits, retries with backoff, timeouts, async and concurrent calls, logging |

### Module 2 — LangChain

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 012 | LangChain Chat Models | The Module 1 chatbot rebuilt on LangChain | chat model classes, message types, invoke/stream/batch |
| 013 | Prompts and Chains | A multi-step chain (summarize, then translate) | prompt templates, LCEL pipe syntax, output parsers, runnables |
| 014 | Structured Output in LangChain | A resume or invoice parser | `with_structured_output`, Pydantic schemas, handling invalid output |
| 015 | Streamlit Chat App | A browser chat UI with streaming | Streamlit basics, session state, chat elements, streaming to the UI |

### Module 3 — Tool Calling

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 016 | Tool Calling by Hand | A weather and calculator assistant using the raw SDK | tool schemas, tool call messages, tool result messages, the call loop |
| 017 | Tools in LangChain | The same assistant with `@tool` and `bind_tools` | tool definitions from functions, parallel tool calls, error handling, `.text` vs `.content` |
| 018 | CLI Calling | An assistant that runs shell commands safely | subprocess, allowlists, confirmation prompts, timeouts, output truncation, risks |

### Module 4 — RAG

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 019 | Embeddings and Similarity | A semantic search over a list of sentences | embeddings, vectors, cosine similarity |
| 020 | Loading and Chunking | A document ingestion script | loaders (PDF, Markdown, web), chunk size and overlap, metadata |
| 021 | Vector Store with Chroma | A persisted, searchable index | Chroma collections, persistence, similarity search, metadata filters |
| 022 | The RAG Chain | Question answering over documents with citations | retrieve-then-generate, grounding prompt, source citation, "I don't know" |
| 023 | Better Retrieval | An improved pipeline compared against 022 | query rewriting, multi-query, MMR, reranking, keyword plus vector search |
| 024 | Evaluating RAG | A test set and a score report | golden questions, retrieval hit rate, faithfulness, LLM-as-judge |
| 025 | Chat With Your Docs | A Streamlit app with upload, chat and sources | file upload, conversational RAG, showing sources in the UI |

### Module 5 — Agents with LangGraph

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 026 | LangGraph Basics | A simple graph with branching | state, nodes, edges, conditional edges, reducers |
| 027 | An Agent from Scratch | A ReAct-style agent as a graph | agent loop, tool node, stop conditions, recursion limit |
| 028 | Memory and Persistence | An agent that resumes conversations | checkpointers, threads, short-term and long-term memory |
| 029 | Human in the Loop | An agent that asks for approval before risky actions | interrupts, resume, editing state, approval flows |
| 030 | Agentic RAG | An agent that decides when and what to retrieve | retrieval as a tool, grading documents, retry and fallback paths |
| 031 | Multi-Agent Systems | A supervisor team and a handoff team built from the same researcher and writer agents | subgraphs, supervisor pattern, handoffs with `Command`, invariants in code, when not to use multi-agent |

### Module 6 — MCP (Model Context Protocol)

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 032 | MCP Concepts and Using a Server | An agent connected to an existing MCP server | hosts, clients, servers, tools/resources/prompts, transports, LangChain MCP adapters |
| 033 | Build Your Own MCP Server | A notes or task-manager server with the Python MCP SDK | defining tools, resources and prompts, testing with the inspector |
| 034 | Agent with Multiple MCP Servers | A LangGraph agent using several servers together | multi-server clients, tool namespacing, trust and security |

### Module 7 — Toward Production

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 035 | Observability and Cost | Tracing and a usage report for an earlier agent | traces, spans, token and cost tracking, debugging agent runs |
| 036 | Safety and Guardrails | Attacks against, then defenses for, an earlier app | prompt injection, input and output validation, provider content filters, least privilege |
| 037 | Capstone | A complete assistant: Streamlit UI, LangGraph agent, RAG, MCP tools, CLI entry point, evaluation | design, integration, a written review against a rubric |

### Module 8 — Beyond the Capstone

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 038 | Evaluating Agents | A scorer for tool-call trajectories | trajectory, right tools / order / arguments, tolerant matching, reports that name the failure |
| 039 | Conversation Memory Strategies | Trimming, summarizing and retrieval over past turns, compared | recall vs tokens per question, lossy summaries, indexing exchanges, setup cost |
| 040 | Context Engineering | A context assembler for an order lookup, measured four ways, plus a position-and-noise experiment | token budget per section, compacting tool results, sub-agent isolation, position and noise in long contexts, accuracy vs tokens per call |
| 041 | Deploying the Capstone | The EXER037 assistant as an HTTP service in a container | configuration from the environment, liveness and readiness, Dockerfile layers, non-root user, no secrets in images |

## 5. Build Phases

| Phase | Deliverable | Notes |
|---|---|---|
| 1. Scaffold | Root config, `aicourse/` package, `.env.example`, README, git repository | Ends with a verified call to the configured provider |
| 2. Lecture site shell | Home page, lecture template, navigation, theme, progress, setup guide | Template reviewed before any content is written |
| 3. Pilot | EXER001–003 and their lectures, complete | Review point: confirm tone, depth and format before scaling |
| 4. Module 1 | EXER004–011 | |
| 5. Modules 2–3 | EXER012–018 | |
| 6. Module 4 | EXER019–025 plus sample documents in `data/` | |
| 7. Module 5 | EXER026–031 | |
| 8. Modules 6–7 | EXER032–037 | |
| 9. Polish | Glossary, cross-links, full run-through of every exercise from a clean clone | |
| 10. Extensions | Quizzes, stretch goals with reference code, worked examples, Module 8 (EXER038–039, and Deploying the Capstone, now EXER041) | Built 2026-11-14. Its planning record, `extended_plan.md`, was removed once done; it is in the git history |
| 11. Context Engineering | EXER040, added to Module 8 after EXER039; Deploying the Capstone moved from 040 to 041 | Follows the Phase D layout: quiz, two stretch goals with reference code |
| 12. Review fixes and Module 9 | Corrections from the course review, a CI workflow, a stronger capstone evaluation, and EXER042–049 (Module 9 — Running in Production) | **Planned, not built.** Scope and checklist in section 8; reasoning in [improvement.md](improvement.md) |

**Definition of done for each exercise**

- The solution runs from a clean `uv sync` using only root configuration.
- `check.py` passes against the solution and fails against the untouched starter (`uv run python check_all.py` verifies this for all exercises).
- The lecture page has all ten sections and its success criteria match the exercise README.
- The lecture has a quiz that passes `check_quizzes.py`, and the README has two stretch goals whose reference code in `stretch/` runs.
- The starter contains enough structure and hints that the learner writes the new concept, not boilerplate.
- Library APIs used are verified against current documentation at build time.

## 6. Assumptions and Decisions

1. **"CLI calling" is covered two ways:** building a command-line app that calls the LLM (EXER010) and letting the LLM run shell commands as a tool (EXER018).
2. **Models:** configurable in `.env`. Recommended defaults: chat `gpt-4.1-mini` (tools, structured output, images, temperature) and embeddings `text-embedding-3-small` on Azure; chat `gemma4:e4b` and embeddings `nomic-embed-text` on Ollama.
3. **Raw SDK:** the `openai` Python SDK pointed at the provider's OpenAI-compatible endpoint is used for the pre-LangChain exercises.
4. **Observability (EXER035):** learners build their own callback-based tracker; LangSmith is an optional, documented add-on (env vars only, no code changes).
5. **Solutions ship in the same repository** as the starters, in `solution/`.
6. **Language:** course content is in English.
7. **Not included:** fine-tuning, model training, and hosting on a cloud platform. EXER041 covers the container image and the health checks a platform needs; pushing the image to a registry and running it on Azure is left to the learner.

## 7. Implementation Notes

- **Providers:** `AICOURSE_PROVIDER` selects `azure` or `ollama`. Provider-specific values are read only in `aicourse/settings.py`, which exposes provider-neutral settings (`base_url`, `api_key`, `chat_model`, `embedding_model`, `max_tokens_param`). Helpers and exercises use only those names (`get_llm_client()`, `get_chat_model()`, `get_embeddings()`), so no code targets a provider or a model.
- **Endpoint:** all code uses the provider's OpenAI-compatible **v1 API** (Azure: `<endpoint>/openai/v1/`; Ollama: `http://localhost:11434/v1/`), so the standard `OpenAI` client and LangChain `ChatOpenAI` / `OpenAIEmbeddings` work with only a `base_url`. No `api_version` handling is needed.
- **Python 3.12**, pinned in `.python-version`. Library versions are locked in `uv.lock` (built with langchain 1.5, langgraph 1.2, openai 3.x, mcp 1.30, chromadb 1.5, streamlit 1.67).
- **Shared package `aicourse/`:** `settings.py` (config), `llm.py` (clients), `rag.py` (knowledge base, chunking, Chroma store and RAG chain used from EXER022 on), `check.py` (check runner), `fakes.py` (fake OpenAI client and fake LangChain chat model, so most checks run offline).
- **Data:** `data/knowledge_base/` holds the fictional *Nimbus Coffee Co.* documents (Markdown, HTML, PDF) used by every RAG and agent exercise; `data/eval_questions.json` is the RAG golden set.
- **Checks:** starters raise `NotImplementedError` in TODOs, so `check.py` reports them as TODO and fails; `--solution` runs the same checks against the reference. Checks marked `[live API]` need a real model.
- **Model compatibility:** the course runs on classic chat models (gpt-4.1 family) and on reasoning models (gpt-5 family, o-series). Reasoning models accept only the default `temperature` and LangChain reaches them through the Responses API, where `AIMessage.content` is a list of blocks. So: optional parameters go through `aicourse.llm.model_params()` (detects support once, caches it in `.aicourse_cache.json`; override with `AICOURSE_SUPPORTS_TEMPERATURE`), and every LangChain answer is read with `.text`, never `.content`. Lectures 004 and 012 teach both points.
- **Offline checks need no `.env`:** the check runner substitutes placeholder settings for checks that are not marked `[live API]`; live checks are skipped with one clear message when the configuration is missing. `--offline` skips live checks on purpose.
- **`check_all.py`** automates the definition of done: every solution passes, every untouched starter fails, and the quizzes are valid.
- **Stretch goals** have reference code in `EXERnnn/stretch/`. It imports the reference solution through `aicourse.stretch.solution_module()` and never modifies it, so `check.py` is unaffected. Stretch code is run by hand, not by `check_all.py`; most of it calls the live model.
- **`aicourse.settings.settings_from_environment()`** loads settings from real environment variables only (EXER041): a deployed service must not depend on a `.env` file.
- **Rules that must always hold are enforced in code, not only in prompts** (example: the EXER031 supervisor cannot finish before the writer has replied).
- **`aicourse.rag.get_vector_store()`** returns one cached store per process, behind a lock: agents run parallel tool calls in threads, and opening the same Chroma folder twice at once fails.
- **MCP exercises** ship their servers inside the exercise folder (`EXER032/servers`, `EXER034/servers`, `EXER037/servers`) so each exercise is self-contained.
- **Lecture site:** `Lecture/assets/js/course.js` is the manifest; `app.js` builds navigation, progress (browser storage), checklists, copy buttons and diagrams. highlight.js 11.9.0 and Mermaid 10.9.1 are vendored for offline use.

## 8. Planned: Review Fixes and Module 9 (Phase 12)

Nothing in this section is built yet. Sections 1–7 describe the course as it exists; this section is the work queue. It comes from the course review in [improvement.md](improvement.md), whose findings were each checked against the files before being accepted.

### Numbering decision

**EXER001–041 keep their numbers. New lessons are appended as EXER042–049.**

- Every new lesson builds on the deployed service (EXER041) or on lessons before it, so appending breaks no prerequisite order. Caching (045) also comes after identity (042) on purpose: a cache key must include the tenant.
- The review suggested teaching Evaluating Agents (038) before the Capstone (037). The swap is not worth a renumber: EXER041 and one EXER038 stretch goal import EXER037 by path, and the same result is reached by adding an in-order tool check to the capstone evaluation (checklist B3) with a forward reference to Lecture 038.
- The review suggested splitting Lecture 040. A split would push Deploying the Capstone to a third number in two days. The time estimate is raised instead (checklist B5).
- Module 8 is renamed, not renumbered: "Beyond the Capstone" becomes "Evaluation, Context and Deployment".

### Module 9 — Running in Production

Each lesson changes the EXER041 service or the EXER037 assistant and follows the standard layout (starter, solution, `check.py`, quiz, two stretch goals with reference code).

| # | Title | The learner builds | Key concepts |
|---|---|---|---|
| 042 | Identity and Tenant Boundaries | Bearer-token authentication on `/ask`; threads, notes and memory bound to the authenticated user; a test that user A cannot read or continue user B's thread | authentication vs authorization, identity from the credential and never from request JSON, per-user namespaces, server-side authorization of every stateful tool, permission-aware retrieval (filter documents by who may read them) |
| 043 | Safe Side Effects | A refund tool that is safe to retry, and an agent run that is killed mid-tool and resumed without paying twice | idempotency keys, at-least-once execution, what a checkpoint replays on resume, separating "decide" from "commit", an audit record per side effect |
| 044 | Operating Under Load | A concurrency limit and bounded queue in front of the service, graceful shutdown, and a local load test with a report | backpressure, HTTP 429/503 and `Retry-After`, deadlines and cancellation, per-user quotas and token budgets, p50/p95/p99, SLIs and SLOs, `SIGTERM` handling as process 1, HTTP 413 for oversized bodies |
| 045 | Caching and Batch Work | An exact-match response cache and a measured prompt-prefix cache experiment on the helpdesk | cache keys (model, prompt version, tools, policy, tenant), invalidation, why semantic caches return wrong answers, stable prefixes for provider prompt caching, hit rate vs stale-answer rate, batch endpoints for offline work |
| 046 | Model Selection and Routing | The existing evaluations run against two models, then a deterministic router with a fallback | quality vs latency vs cost per task, structured-output and tool-call reliability, cheap-first with escalation, provider fallback, re-evaluating when a model is retired or upgraded |
| 047 | Privacy and Data Lifecycle | Deletion of one user's conversations, memory, notes and vector entries, with a check that retrieval and logs no longer expose them | data minimization before the model call, redaction in traces, retention periods, provider retention settings, deletion across stores, indexes, caches and backups |
| 048 | Release-Gated Evaluation | A workflow that compares evaluation results with an approved baseline and fails on a per-category regression | prompts as versioned artifacts, baselines, per-category thresholds, deterministic gate vs manually triggered live evaluation, reports as build artifacts |
| 049 | Learning from Production | A pipeline from user feedback and traces to new evaluation cases | thumbs up/down and implicit signals, sampling traces for review, turning a failure into a regression case, watching quality and cost drift over time |

Still out of scope (unchanged from section 6): fine-tuning and LoRA, quantization, model-serving internals, audio and real-time interfaces, managed-cloud walkthroughs.

### Checklist

**A. Corrections to existing content** (small, do first)

- [ ] A1. Lecture 041 and `EXER041/solution/Dockerfile`: stop claiming exec-form `CMD` gives a clean shutdown. The service has no `SIGTERM` handler, and a process 1 without one ignores the signal, so `docker stop` waits its 10 seconds and then kills. Reword now; the handler itself is built in EXER044.
- [ ] A2. Lecture 024: reword "reasoning before score … improves judgments". Keep the short justification as a diagnostic, say it is not ground truth.
- [ ] A3. Lecture 024: state that the exercise's 1–5 faithfulness score is a simplification and not the claim-level proportion RAGAS defines.
- [ ] A4. Lecture 008: delimiters "separate instructions from data; not a prompt-injection defence by themselves (Lecture 036)".
- [ ] A5. `EXER020/starter/ingest.py`: make the `load_html` docstring raw so `\s` no longer raises a `SyntaxWarning`.
- [ ] A6. Run every stretch goal's reference code on Ollama (the one open item carried over from `extended_plan.md`).

**B. Structure and assessment**

- [ ] B1. Add `.github/workflows/checks.yml`: `uv sync --frozen`, then `uv run python check_all.py --offline`, on every push and pull request.
- [ ] B2. Rename Module 8 to "Evaluation, Context and Deployment" in `course.js`, `quizzes.js` (comment), `README.md` and this file.
- [ ] B3. Capstone evaluation: grow `EXER037/eval_set.json` from 8 cases to about 24, tagged by category (grounding, refusal, arithmetic, memory, tool use, safety); report a score per category; keep a small held-out file; add an optional in-order tool check with a pointer to Lecture 038. Update the 80% rule in the README and rubric to per-category.
- [ ] B4. Judge calibration: add 15–20 human-labelled answers to EXER024 and report exact and adjacent agreement of the judge with them (as a third stretch-style lab or a replacement for goal 1).
- [ ] B5. Raise the Lecture 040 estimate from 75 to 105 minutes; re-time Lectures 036 and 041.
- [ ] B6. Transfer tasks: one unscaffolded task at the end of Modules 1, 4, 5 and 8, each with a short manual checklist and no starter.

**C. Module 9** (one box per lesson; each closes only when the definition of done in section 5 holds)

- [ ] C1. EXER042 Identity and Tenant Boundaries
- [ ] C2. EXER043 Safe Side Effects
- [ ] C3. EXER044 Operating Under Load
- [ ] C4. EXER045 Caching and Batch Work
- [ ] C5. EXER046 Model Selection and Routing
- [ ] C6. EXER047 Privacy and Data Lifecycle
- [ ] C7. EXER048 Release-Gated Evaluation
- [ ] C8. EXER049 Learning from Production

**D. After Module 9**

- [ ] D1. Update sections 1–7 of this file, `README.md`, `course.js`, the glossary and the home page for 49 exercises in 10 modules.
- [ ] D2. Rewrite the Lecture 041 Discussion answer "What is still missing before real customers could use this?" to point at Lectures 042–048.
- [ ] D3. `check_all.py` on both providers: 49/49.
