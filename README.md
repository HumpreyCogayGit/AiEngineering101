# AI Engineer: Zero to Hero

A hands-on course that takes you from your first LLM API call to production-style
agents: messages, streaming, structured output, tool calling, CLI tools, RAG,
LangGraph agents, MCP, observability, guardrails and evaluation.

37 lectures and 37 exercises in 8 modules, built on **Azure Foundry**,
**LangChain**, **LangGraph**, **Chroma** and **Streamlit**.

## Quick start

```bash
# 1. Install uv (https://docs.astral.sh/uv/) and the course dependencies
uv sync

# 2. Configure your Azure Foundry deployment
cp .env.example .env        # then edit .env

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
│   ├── llm.py                 get_openai_client(), get_chat_model(), get_embeddings(), model_params()
│   ├── rag.py                 knowledge-base loading, chunking, Chroma store, RAG chain
│   ├── check.py               the runner used by every EXERxxx/check.py
│   └── fakes.py               fake models so checks can run offline
├── data/                      Nimbus Coffee Co. knowledge base + RAG eval questions
├── EXER001/ … EXER037/        one folder per exercise
└── Lecture/                   the lecture site (plain HTML/CSS/JS, works offline)
```

Each exercise folder:

```
EXER005/
├── README.md     brief: goal, tasks, how to run, success criteria
├── starter/      your code: complete the TODOs
├── solution/     reference solution
└── check.py      automated checks for the success criteria
```

Always run commands from the repository root:

```bash
uv run python EXER005/starter/chatbot.py      # run your code
uv run python EXER005/check.py                # check your code
uv run python EXER005/check.py --solution     # check the reference solution
uv run python EXER005/check.py -v             # show full tracebacks
uv run python EXER005/check.py --offline      # skip the checks that call your deployment
uv run streamlit run EXER015/starter/app.py   # Streamlit exercises
```

Checks marked `[live API]` call your Azure deployment. All others run offline and
need neither a network connection nor a `.env`, so you can start before Azure is set up.

Check the whole course at once:

```bash
uv run python check_all.py              # every solution must pass, every starter must fail
uv run python check_all.py --offline    # the same without live API calls (free; use this in CI)
uv run python check_all.py 16 17        # only these exercises
uv run python check_all.py --mine       # progress report for YOUR code in every starter/
```

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

## Requirements

- macOS, Linux or Windows; a terminal
- An Azure subscription with a Foundry resource, one chat deployment (recommended `gpt-4.1-mini`)
  and one embedding deployment (recommended `text-embedding-3-small`)
- Any chat model with tool calling, structured output and image input works. The course is tested on a
  classic model (`gpt-4.1-mini`) and on a reasoning model (gpt-5 family). Reasoning models only accept
  the default `temperature`; the course detects that and leaves the parameter out (Lecture 004)
- Optional: Node.js (MCP Inspector), a LangSmith account (tracing in EXER035)

See [Plan.MD](Plan.MD) for the course design.
