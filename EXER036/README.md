# EXER036 — Safety and Guardrails

**Module 7 · Toward Production** · Lecture: [Lecture/lectures/lec036.html](../Lecture/lectures/lec036.html)

## Goal

Attack an LLM app with prompt injection, watch it fail, then defend it with
layered guardrails: input checks, PII redaction, safe delimiting, content
filter handling and output checks.

## The project

An email summarizer whose system prompt contains a secret discount code.
[attacks.json](attacks.json) has 6 attack emails and 2 benign ones.

## Tasks

1. Run the starter with only `naive_summarize` and see what leaks (comment out the GUARDED loop).
2. Complete the TODOs in `starter/guardrails.py`: `INJECTION_PATTERNS`, `detect_injection`,
   `redact_pii`, `wrap_untrusted`, `check_output`, `safe_summarize`.

## Run it

```bash
uv run python EXER036/starter/guardrails.py
uv run python EXER036/check.py
```

## Success criteria

- [ ] You ran the naive summarizer and noted which attacks leak the secret (a strong model
      may resist all of them: that is one model on eight known attacks, not a guarantee)
- [ ] The guarded summarizer leaks nothing and does not block the benign emails
- [ ] You can name which layer stopped each attack (hint: the exfiltration email gets past
      the input heuristics — which layer catches it?)
- [ ] All 10 checks pass

> Guardrails reduce risk; they don't remove it. The strongest defence is design:
> don't put secrets in prompts, and don't give a model that reads untrusted text
> tools that can do damage.
