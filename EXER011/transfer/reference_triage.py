"""EXER011 transfer task — reference answer: an IT ticket triager, built from scratch.

    uv run python EXER011/transfer/reference_triage.py

Read this only after you have built your own. It is one reasonable answer, not
the only one. What it combines from Module 1:

- a prompt with explicit definitions and two few-shot examples (EXER008)
- structured output into a Pydantic model, so the result is data (EXER009)
- retries with backoff around every call, SDK retries switched off (EXER011)
- concurrent calls with a limit, results kept in input order (EXER011)
- a labelled set and a per-field accuracy report, so "it works" is a number (EXER008)
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from aicourse.llm import get_async_llm_client, model_params
from aicourse.settings import get_settings

TICKETS = Path(__file__).resolve().parent / "tickets.json"


class Triage(BaseModel):
    system: Literal["network", "email", "payroll", "hardware", "security"]
    severity: Literal["low", "medium", "high", "critical"]
    needs_human: bool = Field(description="true when an engineer must act; false when a self-service fix or a queue is enough")


SYSTEM = """You triage IT helpdesk tickets for a coffee company with several offices.

system: network (VPN, Wi-Fi, internet), email (mailboxes, Outlook, signatures), payroll (payslips,
salary system), hardware (laptops, printers, screens), security (phishing, malware, accounts, MFA).

severity:
- critical: many people cannot work, money or data is at risk right now
- high: one important function is broken, or a security incident with one person
- medium: something works badly but there is a workaround
- low: a request or a minor annoyance

needs_human: true for security incidents, account changes, anything critical, and payroll errors
that change what someone is paid. false when the user can fix it or it can wait in the normal queue."""

EXAMPLES = [
    ("The guest Wi-Fi password on the welcome screen is out of date.",
     Triage(system="network", severity="low", needs_human=False)),
    ("Someone is logged in to my account from another country right now.",
     Triage(system="security", severity="high", needs_human=True)),
]


def messages_for(ticket: str) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM}]
    for text, label in EXAMPLES:
        messages += [{"role": "user", "content": f"<ticket>{text}</ticket>"},
                     {"role": "assistant", "content": label.model_dump_json()}]
    return messages + [{"role": "user", "content": f"<ticket>{ticket}</ticket>"}]


async def triage(client, ticket: str, attempts: int = 4) -> Triage:
    for attempt in range(1, attempts + 1):
        try:
            completion = await client.chat.completions.parse(
                model=get_settings().chat_model, messages=messages_for(ticket),
                response_format=Triage, **model_params(temperature=0))
            return completion.choices[0].message.parsed
        except Exception as exc:  # a real client retries only temporary errors (EXER011's RETRYABLE)
            if attempt == attempts:
                raise
            await asyncio.sleep(0.5 * 2 ** (attempt - 1))
    raise AssertionError("unreachable")


async def main() -> None:
    rows = json.loads(TICKETS.read_text(encoding="utf-8"))
    client = get_async_llm_client().with_options(max_retries=0)
    limit = asyncio.Semaphore(4)

    async def one(ticket: str) -> Triage:
        async with limit:
            return await triage(client, ticket)

    results = await asyncio.gather(*(one(r["text"]) for r in rows))
    fields = ("system", "severity", "needs_human")
    correct = {f: 0 for f in fields}
    for row, got in zip(rows, results):
        wrong = [f for f in fields if getattr(got, f) != row["label"][f]]
        for f in fields:
            correct[f] += f not in wrong
        mark = "ok  " if not wrong else "MISS"
        print(f"{mark} {row['text'][:58]:<58} " + (", ".join(f"{f}={getattr(got, f)} (want {row['label'][f]})" for f in wrong)))
    print()
    for f in fields:
        print(f"{f:<12} {correct[f]}/{len(rows)}  {correct[f] / len(rows):.0%}")
    print("\nSeverity is the hard field: its boundaries are a judgment. Look at the misses before changing the prompt.")


if __name__ == "__main__":
    asyncio.run(main())
