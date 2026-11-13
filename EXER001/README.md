# EXER001 — Setup and First Check

**Module 0 · Foundations** · Lecture: [Lecture/lectures/lec001.html](../Lecture/lectures/lec001.html)

## Goal

Get a working development environment and prove that your configuration loads
correctly — without ever printing your secret key.

## Before you start

Follow the setup guide: [Lecture/setup.html](../Lecture/setup.html). You need:

1. `uv` installed, then `uv sync` run once from the repository root.
2. An inference provider with a **chat model**, either:
   - an Azure Foundry resource with a chat model deployment (recommended: `gpt-4.1-mini`; reasoning models such as the gpt-5 family work too), or
   - Ollama running locally with a chat model pulled (recommended: `ollama pull gemma4:e4b`).
3. A `.env` file at the repository root, copied from `.env.example`, with `AICOURSE_PROVIDER` set to `azure` or `ollama` and that provider's block filled in.

## Tasks

Open `starter/check_setup.py` and complete the three `TODO` functions:

| Function | What it must do |
|---|---|
| `python_version_ok()` | Return `True` when Python is 3.12 or newer |
| `masked_key(key)` | Hide a secret: keep the first 4 and last 4 characters, replace the middle with `****`. Keys of 12 characters or fewer become just `****` |
| `load_config()` | Return the course settings using `aicourse.settings.get_settings()` |

## Run it

```bash
uv run python EXER001/starter/check_setup.py
```

## Check it

```bash
uv run python EXER001/check.py              # checks your starter/ code
uv run python EXER001/check.py --solution   # checks the reference solution
```

## Success criteria

- [ ] `uv sync` completes and `uv run python --version` shows 3.12.x
- [ ] `.env` exists at the repository root and is ignored by git
- [ ] `check_setup.py` prints your provider, endpoint and model names, with the key masked
- [ ] All checks in `check.py` pass
