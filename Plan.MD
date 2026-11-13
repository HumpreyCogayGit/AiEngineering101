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
├── check_all.py              # Runs every exercise check: solutions pass, starters fail
├── aicourse/                 # Small shared package, installed in editable mode
│   ├── settings.py           # Loads and validates .env (pydantic-settings)
│   ├── llm.py                # get_chat_model(), get_embeddings() helpers
│   └── check.py              # Helpers used by exercise checks
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
├── README.md        # Short brief: goal, tasks, how to run, success criteria, link to lecture
├── starter/         # Code with TODOs for the learner to complete
├── solution/        # Reference solution
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
    ├── js/app.js         # Sidebar, previous/next, progress, theme, copy buttons
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
9. **Further Reading** — official documentation links

**Site features**

- Sidebar navigation and previous/next links generated from `course.js`, so adding a lecture means adding one entry and one HTML file.
- Syntax highlighting, copy button on code blocks, Mermaid diagrams for flows (message loop, RAG pipeline, agent graph).
- Light and dark theme, readable on mobile.
- "Mark as complete" per lecture, stored in the browser, with a progress bar on the home page.
- Libraries are stored in `assets/vendor/` so the site works offline and from `file://`.

## 4. Curriculum

37 exercises in 8 modules. Lecture `lecNNN.html` pairs with `EXERNNN`.

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

**Definition of done for each exercise**

- The solution runs from a clean `uv sync` using only root configuration.
- `check.py` passes against the solution and fails against the untouched starter (`uv run python check_all.py` verifies this for all exercises).
- The lecture page has all nine sections and its success criteria match the exercise README.
- The starter contains enough structure and hints that the learner writes the new concept, not boilerplate.
- Library APIs used are verified against current documentation at build time.

## 6. Assumptions and Decisions

1. **"CLI calling" is covered two ways:** building a command-line app that calls the LLM (EXER010) and letting the LLM run shell commands as a tool (EXER018).
2. **Models:** configurable in `.env`. Recommended defaults: chat `gpt-4.1-mini` (tools, structured output, images, temperature) and embeddings `text-embedding-3-small` on Azure; chat `gemma4:e4b` and embeddings `nomic-embed-text` on Ollama.
3. **Raw SDK:** the `openai` Python SDK pointed at the provider's OpenAI-compatible endpoint is used for the pre-LangChain exercises.
4. **Observability (EXER035):** learners build their own callback-based tracker; LangSmith is an optional, documented add-on (env vars only, no code changes).
5. **Solutions ship in the same repository** as the starters, in `solution/`.
6. **Language:** course content is in English.
7. **Not included:** fine-tuning, model training, cloud deployment of the apps. Deployment (containers, Azure hosting) could be added as an extra module after the capstone.

## 7. Implementation Notes

- **Providers:** `AICOURSE_PROVIDER` selects `azure` or `ollama`. Provider-specific values are read only in `aicourse/settings.py`, which exposes provider-neutral settings (`base_url`, `api_key`, `chat_model`, `embedding_model`, `max_tokens_param`). Helpers and exercises use only those names (`get_llm_client()`, `get_chat_model()`, `get_embeddings()`), so no code targets a provider or a model.
- **Endpoint:** all code uses the provider's OpenAI-compatible **v1 API** (Azure: `<endpoint>/openai/v1/`; Ollama: `http://localhost:11434/v1/`), so the standard `OpenAI` client and LangChain `ChatOpenAI` / `OpenAIEmbeddings` work with only a `base_url`. No `api_version` handling is needed.
- **Python 3.12**, pinned in `.python-version`. Library versions are locked in `uv.lock` (built with langchain 1.5, langgraph 1.2, openai 3.x, mcp 1.30, chromadb 1.5, streamlit 1.67).
- **Shared package `aicourse/`:** `settings.py` (config), `llm.py` (clients), `rag.py` (knowledge base, chunking, Chroma store and RAG chain used from EXER022 on), `check.py` (check runner), `fakes.py` (fake OpenAI client and fake LangChain chat model, so most checks run offline).
- **Data:** `data/knowledge_base/` holds the fictional *Nimbus Coffee Co.* documents (Markdown, HTML, PDF) used by every RAG and agent exercise; `data/eval_questions.json` is the RAG golden set.
- **Checks:** starters raise `NotImplementedError` in TODOs, so `check.py` reports them as TODO and fails; `--solution` runs the same checks against the reference. Checks marked `[live API]` need a real model.
- **Model compatibility:** the course runs on classic chat models (gpt-4.1 family) and on reasoning models (gpt-5 family, o-series). Reasoning models accept only the default `temperature` and LangChain reaches them through the Responses API, where `AIMessage.content` is a list of blocks. So: optional parameters go through `aicourse.llm.model_params()` (detects support once, caches it in `.aicourse_cache.json`; override with `AICOURSE_SUPPORTS_TEMPERATURE`), and every LangChain answer is read with `.text`, never `.content`. Lectures 004 and 012 teach both points.
- **Offline checks need no `.env`:** the check runner substitutes placeholder settings for checks that are not marked `[live API]`; live checks are skipped with one clear message when the configuration is missing. `--offline` skips live checks on purpose.
- **`check_all.py`** automates the definition of done: every solution passes, every untouched starter fails.
- **Rules that must always hold are enforced in code, not only in prompts** (example: the EXER031 supervisor cannot finish before the writer has replied).
- **`aicourse.rag.get_vector_store()`** returns one cached store per process, behind a lock: agents run parallel tool calls in threads, and opening the same Chroma folder twice at once fails.
- **MCP exercises** ship their servers inside the exercise folder (`EXER032/servers`, `EXER034/servers`, `EXER037/servers`) so each exercise is self-contained.
- **Lecture site:** `Lecture/assets/js/course.js` is the manifest; `app.js` builds navigation, progress (browser storage), checklists, copy buttons and diagrams. highlight.js 11.9.0 and Mermaid 10.9.1 are vendored for offline use.
