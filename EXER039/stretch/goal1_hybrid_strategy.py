"""EXER039 stretch goal 1 — a hybrid strategy: a profile summary + retrieval.

    uv run python EXER039/stretch/goal1_hybrid_strategy.py

Give each half the job it is good at:

- the SUMMARY is a short customer profile: who she is and what always holds
  (allergy, taste). It is tiny, and it answers questions that need several
  facts at once. It deliberately leaves out one-off details.
- RETRIEVAL fetches the one exchange with the exact detail asked for (an
  order number, an address). It cannot answer a question whose facts are
  spread over the conversation.

    [profile summary] + [the most relevant exchange] + [last exchange]

Six probes ask for one exact detail, two need several facts at once. Each
half alone misses one kind; the hybrid should miss neither.
"""

from __future__ import annotations

import json

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "memory_strategies.py")


def hybrid(history, question, summary: str, index, k: int = 2) -> list[dict]:
    retrieved = base.retrieve_turns(index, question, k=k, keep_last=1)
    return [{"role": "system", "content": base.SUMMARY_PREFIX + summary}] + retrieved


BROAD_PROBES = [
    {"question": "What should a barista know about this customer before making her a drink?",
     "expect_keywords": ["nut", "light"]},
    {"question": "Give the customer's name, her company and her job in one sentence.",
     "expect_keywords": ["rina", "lumen", "office manager"]},
]


def profile_summary(llm, history) -> str:
    """Who the customer is and what always holds. No order numbers, addresses, dates or prices."""
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    return llm.invoke([
        ("system", "Write a customer profile in at most 30 words: name, company, job, allergies and taste "
                   "preferences. Leave out everything else: no orders, numbers, addresses, dates or emails."),
        ("user", transcript),
    ]).text.strip()


def main() -> None:
    data = json.loads(base.CONVERSATION.read_text(encoding="utf-8"))
    history, probes = data["turns"], data["probes"] + BROAD_PROBES
    llm = get_chat_model(temperature=0)
    profile = profile_summary(llm, history)
    index = base.TurnIndex(history, base.default_embedder())
    strategies = {
        "profile summary only": lambda h, q: [{"role": "system", "content": base.SUMMARY_PREFIX + profile}],
        "retrieve 1 + last": lambda h, q: base.retrieve_turns(index, q, k=1, keep_last=1),
        "hybrid": lambda h, q: hybrid(h, q, profile, index, k=1),
    }
    print(f"Profile: {profile}\n")
    print(f"{len(probes)} probes: 6 ask for one exact detail, 2 need several facts at once.\n")
    print(f"{'strategy':<24}{'recall':>8}{'tokens/question':>17}   missed")
    for name, strategy in strategies.items():
        r = base.evaluate(llm, strategy, history, probes)
        print(f"{name:<24}{r['recall']:>8.0%}{r['tokens_per_question']:>17}   {'; '.join(q[:30] for q in r['missed']) or '-'}")
    print("\nThe hybrid costs the most tokens per question and is still a fraction of the full history.\n"
          "It is worth it only where the 'missed' columns of the two halves differ: measure before you combine.")


if __name__ == "__main__":
    main()
