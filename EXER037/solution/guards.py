"""Guardrails for the helpdesk (from EXER036, given)."""

from __future__ import annotations

import re

MAX_INPUT_CHARS = 2000
ALLOWED_DOMAINS = {"nimbuscoffee.example"}

INJECTION_PATTERNS = {
    "override": r"\b(ignore|disregard|forget)\b.{0,40}\b(instructions|rules|prompt)",
    "system_impersonation": r"(^|\n)\s*(system|developer|assistant)\s*:",
    "prompt_leak": r"\b(system prompt|your instructions|hidden prompt)\b",
    "jailbreak": r"\b(DAN|jailbreak|no rules|debug mode|developer mode)\b",
}


def check_input(text: str) -> list[str]:
    problems = [name for name, p in INJECTION_PATTERNS.items() if re.search(p, text, re.IGNORECASE | re.DOTALL)]
    if len(text) > MAX_INPUT_CHARS:
        problems.append("too_long")
    return problems


def check_output(text: str) -> list[str]:
    return [f"untrusted_url:{d}" for d in re.findall(r"https?://([^/\s)]+)", text)
            if d.lower() not in ALLOWED_DOMAINS]
