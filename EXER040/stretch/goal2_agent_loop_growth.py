"""EXER040 stretch goal 2 — connect to EXER027: the context of an agent loop grows every step.

    uv run python EXER040/stretch/goal2_agent_loop_growth.py

The EXER027 agent sends the WHOLE message list on every step: system prompt,
tool definitions, the question, and every earlier tool call and tool result.
A tool result read once at step 1 is paid for again on every later step.

This script simulates an 8-step loop (no model calls, so it is free): step 1
calls the order lookup, the later steps call small tools (knowledge base
search, ticket creation) that each add about 150 tokens. It counts the input
tokens of every step for three ways of handling the big order lookup:

    raw         the 38 KB response goes into the history as it is
    compacted   compact_orders() goes into the history
    sub-agent   a sub-agent reads the raw response once; only its findings go in
"""

from __future__ import annotations

import json

from aicourse.stretch import solution_module

base = solution_module(__file__, "context_engineering.py")

STEPS = 8
SMALL_RESULT = "Knowledge base: " + "Standard shipping in Metro Manila takes 1-2 business days. " * 10
FINDINGS = "Findings from the order lookup: N-5129 is in transit with Ninja Van, tracking number on file."


def loop_tokens(first_result: str, side_tokens: int = 0) -> list[int]:
    """Input tokens of each step of the loop."""
    fixed = [("system", base.SYSTEM + "\n" + json.dumps(base.TOOLS)), ("user", "Where is order N-5129, and when will it arrive?")]
    history: list[tuple[str, str]] = []
    per_step = []
    for step in range(1, STEPS + 1):
        per_step.append(base.count_message_tokens(fixed + history))
        history += [("assistant", f"(tool call {step})"), ("tool", first_result if step == 1 else SMALL_RESULT)]
    per_step[1] += side_tokens  # the sub-agent reads the raw response once, before its findings are first sent
    return per_step


def main() -> None:
    account = json.loads(base.ACCOUNT.read_text(encoding="utf-8"))
    raw = json.dumps(account, ensure_ascii=False)
    sub_cost = base.count_tokens(base.SUBAGENT_PROMPT) + base.count_tokens(raw) + base.count_tokens(FINDINGS) + 20
    rows = {
        "raw": loop_tokens(raw),
        "compacted": loop_tokens(base.compact_orders(account)),
        "sub-agent": loop_tokens(FINDINGS, side_tokens=sub_cost),
    }
    print("Input tokens sent at each step of an 8-step agent loop:\n")
    print(f"{'step':>4}" + "".join(f"{name:>12}" for name in rows))
    for i in range(STEPS):
        print(f"{i + 1:>4}" + "".join(f"{tokens[i]:>12,}" for tokens in rows.values()))
    print(f"{'sum':>4}" + "".join(f"{sum(tokens):>12,}" for tokens in rows.values()))
    raw_total, sub_total = sum(rows["raw"]), sum(rows["sub-agent"])
    print(f"\nThe raw response is read again on every step after it arrives ({STEPS - 1} times). The sub-agent reads it once: over the whole loop it "
          f"sends {raw_total / sub_total:.1f}x fewer tokens than the raw history,\n"
          "although step 2, where it reads the raw response, costs slightly more than the raw dump.")


if __name__ == "__main__":
    main()
