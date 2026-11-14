"""EXER039 stretch goal 2 — count the setup cost too, and find the break-even point (EXER035).

    uv run python EXER039/stretch/goal2_setup_cost.py

"Tokens per question" flatters the summary and the index: both cost
something BEFORE the first question. The summary call reads the whole
history once; the index embeds every exchange once. Spread over the
questions asked afterwards, that cost shrinks:

    total tokens after n questions = setup + n x tokens per question

The break-even point is the number of questions after which a strategy has
cost less than resending the full history every time.
"""

from __future__ import annotations

import json
import math

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "memory_strategies.py")


def break_even(setup: int, per_question: int, full_per_question: int) -> int | None:
    """Questions needed before `setup + n * per_question` drops below `n * full_per_question`."""
    saved = full_per_question - per_question
    return math.floor(setup / saved) + 1 if saved > 0 else None


def main() -> None:
    data = json.loads(base.CONVERSATION.read_text(encoding="utf-8"))
    history = data["turns"]
    question = data["probes"][0]["question"]
    llm = get_chat_model(temperature=0)

    summary = base.summarize(llm, history[:-4])
    index = base.TurnIndex(history, base.default_embedder())
    full = base.count_tokens(history)
    rows = {
        # name: (setup tokens, tokens per question, what the setup is)
        "full history": (0, full, "-"),
        "trim (400 tok)": (0, base.count_tokens(base.trim_recent(history, 400)), "-"),
        "summary + last 4": (base.count_tokens(history[:-4]) + base.count_tokens([{"content": summary}]),
                             base.count_tokens(base.summary_and_recent(history, summary, 4)),
                             "one chat call: reads the history, writes the summary"),
        "retrieve 3 + last": (base.count_tokens([{"content": t} for t in index.texts]),
                              base.count_tokens(base.retrieve_turns(index, question, 3, 1)),
                              "one embedding call (embedding tokens are far cheaper than chat tokens)"),
    }
    print(f"{'strategy':<20}{'setup':>7}{'per question':>14}{'after 1':>9}{'after 10':>10}{'break-even':>12}")
    for name, (setup, per_question, _) in rows.items():
        point = break_even(setup, per_question, full) if setup else None
        print(f"{name:<20}{setup:>7}{per_question:>14}{setup + per_question:>9}{setup + 10 * per_question:>10}"
              f"{(str(point) + ' questions') if point else '-':>12}")
    print()
    for name, (setup, _, what) in rows.items():
        if setup:
            print(f"{name}: setup = {what}")
    print("\nAfter one question the summary has cost MORE than the full history. It pays off from the second question on,\n"
          "and every new turn of the conversation makes the full history more expensive while the summary stays small.")


if __name__ == "__main__":
    main()
