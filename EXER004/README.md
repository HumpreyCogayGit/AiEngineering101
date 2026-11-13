# EXER004 — The SDK and Model Parameters

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec004.html](../Lecture/lectures/lec004.html)

## Goal

Replace hand-written HTTP with the `openai` Python SDK, the client library for the
OpenAI-compatible API every provider in this course speaks, and learn the
parameters that shape a response: `temperature`, the answer length limit, tokens
and cost.

## Tasks

Complete the TODOs in `starter/sdk_basics.py`:

| Function | What it must do |
|---|---|
| `make_client()` | Build an `OpenAI` client using `base_url` and `api_key` from settings |
| `ask(client, prompt, temperature, max_tokens)` | Call `chat.completions.create` and return a `CompletionResult` |
| `count_tokens(text)` | Count tokens locally with `tiktoken` |
| `estimate_cost(...)` | Turn token counts into dollars (prices per 1M tokens) |
| `temperature_experiment(...)` | Ask the same question several times at several temperatures |

## Run it

```bash
uv run python EXER004/starter/sdk_basics.py
uv run python EXER004/check.py
```

## Success criteria

- [ ] The script prints an answer, its token usage and an estimated cost
- [ ] `max_tokens=5` produces a cut-off answer with `finish_reason="length"` (on a reasoning
      model the text can even be empty: the budget went to hidden reasoning tokens)
- [ ] On a classic model the answers are (nearly) identical at temperature 0 and vary at 1.0;
      on a reasoning model temperature 0 is reported as not supported and the script keeps running
- [ ] All 7 checks pass

> **Note:** the length limit has two names. `max_completion_tokens` is the current one and the
> only one reasoning models accept; `max_tokens` is the original one and the only one Ollama
> applies. `get_settings().max_tokens_param` gives the right name for your provider.

> **Note:** reasoning models (o-series, gpt-5 family) only accept the default `temperature`
> and answer anything else with a 400 error. `temperature_experiment()` must survive that:
> catch `BadRequestError` and store an empty list for a temperature the model rejects.
