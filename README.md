# AI Engineering: Building with LLMs

A hands-on course that takes you from your first LLM API call to production-style
agents: messages, streaming, structured output, tool calling, CLI tools, RAG,
LangGraph agents, MCP, observability, guardrails and evaluation, and then the work of
running them in production: identity, safe side effects, load, caching, privacy and release gates.

49 lectures and 49 exercises in 10 modules, built on **LangChain**, **LangGraph**,
**Chroma** and **Streamlit**. The models run on the inference provider you choose:
**Azure Foundry** in the cloud or **Ollama** on your own machine.

## Quick start

```bash
# 1. Install uv (https://docs.astral.sh/uv/) and the course dependencies
uv sync

# 2. Choose your inference provider and configure it
cp .env.example .env        # then edit .env (see "Inference providers" below)

# 3. Verify
uv run python EXER001/solution/check_setup.py

# 4. Open the lecture site
open Lecture/index.html     # Windows: start Lecture\index.html
```

Full instructions: [Lecture/setup.html](Lecture/setup.html).

## How it's organized

```
AiEngineerCourse/
├── pyproject.toml / uv.lock   all dependencies, shared by every exercise
├── .env.example               configuration template (copy to .env)
├── aicourse/                  small shared package
│   ├── settings.py            loads + validates .env (the only place config is read)
│   ├── llm.py                 get_llm_client(), get_chat_model(), get_embeddings(), model_params()
│   ├── rag.py                 knowledge-base loading, chunking, Chroma store, RAG chain
│   ├── check.py               the runner used by every EXERxxx/check.py
│   ├── fakes.py               fake models so checks can run offline
│   └── stretch.py             lets stretch-goal code build on a reference solution
├── data/                      Nimbus Coffee Co. knowledge base + RAG eval questions
├── EXER001/ … EXER049/        one folder per exercise
├── check_all.py               checks every exercise, and the lecture quizzes
├── check_quizzes.py           validates the self-check quizzes of the lecture site
└── Lecture/                   the lecture site (plain HTML/CSS/JS, works offline)
```

Each exercise folder:

```
EXER005/
├── README.md     brief: goal, tasks, how to run, success criteria, stretch goals
├── starter/      your code: complete the TODOs
├── solution/     reference solution
├── stretch/      reference code for the two optional stretch goals
└── check.py      automated checks for the success criteria
```

Modules 1, 4, 5 and 8 end with a **transfer task** in the last exercise's README (EXER011, EXER025, EXER031,
EXER041): a new problem in a new domain, with no starter code and no checks, and a reference answer in
its `transfer/` folder.

Every exercise ends with two optional **stretch goals**: one extends the exercise, one connects it to
another exercise. They are never needed for "complete". Each has runnable reference code in `stretch/`
that builds on `solution/` without changing it, so the checks are unaffected.

Every lecture page has a **Check Yourself** quiz (four or five multiple-choice questions, with an
explanation for every option). It runs offline in the browser; the score is shown on the course home
page and never blocks "Mark as complete". The questions are data in `Lecture/assets/js/quizzes.js`.

Always run commands from the repository root:

```bash
uv run python EXER005/starter/chatbot.py      # run your code
uv run python EXER005/check.py                # check your code
uv run python EXER005/check.py --solution     # check the reference solution
uv run python EXER005/check.py -v             # show full tracebacks
uv run python EXER005/check.py --offline      # skip the checks that call your model
uv run streamlit run EXER015/starter/app.py   # Streamlit exercises
```

Checks marked `[live API]` call your chat or embedding model. All others run offline and
need neither a network connection nor a `.env`, so you can start before your provider is set up.

Check the whole course at once:

```bash
uv run python check_all.py              # every solution must pass, every starter must fail; quizzes are validated
uv run python check_all.py --offline    # the same without live API calls (free; use this in CI)
uv run python check_all.py 16 17        # only these exercises
uv run python check_all.py --mine       # progress report for YOUR code in every starter/
```

The offline check runs on every push and pull request in GitHub Actions
([.github/workflows/checks.yml](.github/workflows/checks.yml)).

## Inference providers

`AICOURSE_PROVIDER` in `.env` selects where the models run. Both providers speak the same
OpenAI-compatible API, so every exercise, check and helper is identical on both; only `.env` differs.

| | `azure` (default) | `ollama` |
|---|---|---|
| Runs | in the cloud, pay per token | on your machine, free, works offline |
| Configure | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | nothing required; optional `OLLAMA_BASE_URL`, `OLLAMA_CHAT_MODEL`, `OLLAMA_EMBEDDING_MODEL` |
| Default models | the deployments you name | `gemma4:e4b` and `nomic-embed-text:latest` |

To use Ollama:

```bash
ollama pull gemma4:e4b
ollama pull nomic-embed-text
# in .env:  AICOURSE_PROVIDER=ollama
uv run python EXER001/solution/check_setup.py
```

Code never names a provider. It asks `aicourse.settings` for `base_url`, `api_key`, `chat_model`
and `embedding_model`, and `aicourse.llm` for `get_llm_client()`, `get_chat_model()` and
`get_embeddings()`. Adding a provider means adding one block to `aicourse/settings.py`.

Things that differ between providers, and how the course handles them:

- **Answer length limit**: Azure applies `max_completion_tokens`, Ollama applies `max_tokens`.
  Use `model_params(max_tokens=...)` or `settings.max_tokens_param`.
- **API key**: a local Ollama does not check it.
- **Thinking**: `model_params()` and `get_chat_model()` send `reasoning_effort` only when you set
  `AICOURSE_REASONING_EFFORT`. Leave it unset: `none` makes a local model much faster, but `gemma4:e4b`
  then fails the agent checks in EXER017, EXER030 and EXER031.
- **Structured output**: Azure shows your field descriptions to the model; Ollama only enforces the shape.
  State rules about values (date formats) in the prompt too.
- **Embedding prefixes**: `get_embeddings()` adds the query/document prefixes an embedding model was trained
  with (`OLLAMA_EMBEDDING_QUERY_PREFIX`, `OLLAMA_EMBEDDING_DOCUMENT_PREFIX`; the defaults suit `nomic-embed-text`).
- **Vector stores**: each embedding model gets its own Chroma collection, so switching provider
  rebuilds the index on first use instead of mixing incompatible vectors.
- **Quality**: a small local model follows instructions less reliably than a large hosted one.
  A few `[live API]` checks that grade the model's judgement can fail on a small model
  even when your code is right; `--offline` checks never depend on the model.

## Curriculum

| Module | Exercises | Topics |
|---|---|---|
| 0 · Foundations | 001–003 | Setup, Python for AI, raw HTTP API calls |
| 1 · Talking to an LLM | 004–011 | SDK and parameters, messages and roles, content blocks, streaming, prompt engineering, structured output, CLI apps, reliability |
| 2 · LangChain | 012–015 | Chat models, prompts and chains (LCEL), structured output, Streamlit chat |
| 3 · Tool Calling | 016–018 | Tool calling by hand, LangChain tools, safe CLI/shell calling |
| 4 · RAG | 019–025 | Embeddings, loading and chunking, Chroma, the RAG chain, better retrieval, RAG evaluation, chat with your docs |
| 5 · Agents with LangGraph | 026–031 | Graph basics, ReAct agent, memory and persistence, human in the loop, agentic RAG, multi-agent |
| 6 · MCP | 032–034 | MCP concepts and clients, building a server, multi-server agents |
| 7 · Toward Production | 035–037 | Observability and cost, safety and guardrails, capstone |
| 8 · Evaluation, Context and Deployment | 038–041 | Evaluating agents (tool-call trajectories), conversation memory strategies, context engineering (token budgets, compacting tool results, sub-agent isolation, position and noise), deploying the capstone in a container |
| 9 · Running in Production | 042–049 | Identity and tenant boundaries, safe side effects (idempotency), operating under load (limits, SLOs, graceful shutdown), caching and batch work, model selection and routing, privacy and data lifecycle, release-gated evaluation, learning from production |

## Requirements

- macOS, Linux or Windows; a terminal
- One inference provider:
  - **Azure Foundry**: an Azure subscription with a Foundry resource, one chat deployment
    (recommended `gpt-4.1-mini`) and one embedding deployment (recommended `text-embedding-3-small`), or
  - **Ollama**: [Ollama](https://ollama.com) installed locally with a chat model (recommended `gemma4:e4b`,
    about 10 GB) and an embedding model (recommended `nomic-embed-text`)
- Any chat model with tool calling, structured output and image input works. The course is tested on a
  classic model (`gpt-4.1-mini`), on a reasoning model (gpt-5 family) and on a local model (`gemma4:e4b`). Reasoning models only accept
  the default `temperature`; the course detects that and leaves the parameter out (Lecture 004)
- Optional: Node.js (MCP Inspector), a LangSmith account (tracing in EXER035), Docker (building the images in EXER041 and EXER044)

See [Plan.MD](Plan.MD) for the course design.
