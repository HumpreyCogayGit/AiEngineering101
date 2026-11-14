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

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Make `check_setup.py` report whether the embedding model is reachable, not only configured. *Done when:* the script prints `Reachable : yes (N dimensions)`, or `NO` with the reason, and never crashes. It needs one HTTP request, so come back to it after EXER003 if that is new.
2. **Connect.** Print where each setting came from: a real environment variable, `.env`, or the default in `aicourse/settings.py`. *Done when:* running with `AICOURSE_REQUEST_TIMEOUT=5` in front of the command changes that one line from `default` to `environment`.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER001/stretch/goal1_embedding_reachable.py
uv run python EXER001/stretch/goal2_setting_sources.py
```
