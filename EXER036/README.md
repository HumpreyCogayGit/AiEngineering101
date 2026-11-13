# EXER036 — Safety and Guardrails

**Module 7 · Toward Production** · Lecture: [Lecture/lectures/lec036.html](../Lecture/lectures/lec036.html)

## Goal

Attack an LLM app with prompt injection, watch it fail, then defend it with
layered guardrails: input checks, PII redaction, safe delimiting, content
filter handling and output checks.

## The project

An email summarizer whose system prompt contains a secret discount code.
[attacks.json](attacks.json) has 9 attack emails and 2 benign ones. Five attacks are blatant
("ignore all previous instructions"). Four are stealthy: they read like ordinary customer
emails, pass the input heuristics, and try to get the secret or an attacker's link into
the summary.

## Tasks

1. Run the starter with only `naive_summarize` and see what gets through (comment out the
   GUARDED loop). The suite marks a summary `LEAKED!` when it contains the secret and
   `UNSAFE!` when it carries a link to a domain you don't trust.
2. Complete the TODOs in `starter/guardrails.py`: `INJECTION_PATTERNS`, `detect_injection`,
   `redact_pii`, `wrap_untrusted`, `check_output`, `safe_summarize`.

## Run it

```bash
uv run python EXER036/starter/guardrails.py
uv run python EXER036/check.py
```

## Success criteria

- [ ] You ran the naive summarizer and noted which attacks get through. A strong model
      refuses to reveal the secret, yet still carries the phishing link and the tracking
      image into its summary
- [ ] The guarded summarizer exposes nothing (no secret, no untrusted link) and does not
      block the benign emails
- [ ] You can name which layer stopped each attack (hint: the four stealthy emails get past
      the input heuristics — which layers are left?)
- [ ] All 11 checks pass

> Guardrails reduce risk; they don't remove it. The strongest defence is design:
> don't put secrets in prompts, and don't give a model that reads untrusted text
> tools that can do damage.
