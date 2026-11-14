"""EXER040 stretch goal 1 — compact by question.

    uv run python EXER040/stretch/goal1_question_aware.py

compact_orders() keeps every order, because it does not know the question.
When the question names orders ("N-5104"), only those lines are needed. When
it names none ("Which order was cancelled?"), the filter has nothing to go
on and must fall back to the full compact list, or it throws the answer away.

Compared on the same six questions: accuracy and tokens per call.
"""

from __future__ import annotations

import json
import re

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "context_engineering.py")


def compact_for_question(account: dict, question: str) -> str:
    """The header and the lines of the orders the question names; every line when it names none."""
    lines = base.compact_orders(account).splitlines()
    named = set(re.findall(r"N-\d{4}", question))
    if not named:
        return "\n".join(lines)  # the fallback: filtering on nothing would drop the answer
    return "\n".join([lines[0]] + [line for line in lines[1:] if line.split(" | ")[0] in named])


def main() -> None:
    account = json.loads(base.ACCOUNT.read_text(encoding="utf-8"))
    probes = json.loads(base.CASES.read_text(encoding="utf-8"))["probes"]
    llm = get_chat_model(temperature=0)
    compact = base.compact_orders(account)
    builders = {
        "compacted": lambda q: (base.base_sections(compact), 0),
        "compacted by question": lambda q: (base.base_sections(compact_for_question(account, q)), 0),
    }
    print(f"{'context':<24}{'accuracy':>9}{'main tokens':>13}   missed")
    for name, builder in builders.items():
        r = base.evaluate(llm, builder, probes)
        print(f"{name:<24}{r['accuracy']:>9.0%}{r['main_tokens']:>13,}   {'; '.join(q[:34] for q in r['missed']) or '-'}")
    print("\nTokens per question with the filter:")
    for probe in probes:
        q = probe["question"]
        tokens = base.count_tokens(compact_for_question(account, q))
        print(f"  {tokens:>5}  {q}{'   (names no order: full list)' if tokens > 500 else ''}")


if __name__ == "__main__":
    main()
