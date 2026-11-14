"""EXER013 stretch goal 2 — a fallback for a summary that is too long.

    uv run python EXER013/stretch/goal2_fallback_chain.py

"At most 15 words" is a request, not a guarantee. This chain checks the
result in code and, when it is too long, falls back to a stricter chain:

    summarize -> check length --ok--------------------------> summary
                      |
                      +--too long (raises)--> fallback: shorten it

`with_fallbacks` runs the next runnable when the first one raises. The check
is a plain function that raises, which turns "bad output" into an error the
fallback can catch. The first half of the demo is offline and deterministic.
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough

from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "chains.py")


class SummaryTooLong(ValueError):
    pass


shorten_prompt = ChatPromptTemplate.from_messages([
    ("system", "You shorten summaries. Output only the shortened summary: one sentence, "
               "strictly no more than {max_words} words. Count the words before you answer."),
    ("human", "{text}"),
])


def check_length(data: dict) -> str:
    """Return the summary, or raise so that the fallback takes over."""
    words = len(data["summary"].split())
    if words > data["max_words"]:
        raise SummaryTooLong(f"{words} words, limit {data['max_words']}")
    return data["summary"]


def build_safe_summary_chain(llm, on_fallback=None) -> Runnable:
    """{text, max_words} -> a summary; the fallback runs when the first one is too long."""
    primary = RunnablePassthrough.assign(summary=base.build_summary_chain(llm)) | RunnableLambda(check_length)

    def note(data: dict) -> dict:
        if on_fallback:
            on_fallback()
        return data

    fallback = RunnableLambda(note) | shorten_prompt | llm | StrOutputParser()
    # Only our own error triggers the fallback. A network error should still surface.
    return primary.with_fallbacks([fallback], exceptions_to_handle=(SummaryTooLong,))


def main() -> None:
    # 1. Offline: the first scripted reply is too long, the second is the shortened one.
    fake = fake_chat_model(
        "The council approved a plan to turn three downtown garages into buildings with homes and shops.",
        "Council approves converting three garages into housing.",
    )
    used = []
    chain = build_safe_summary_chain(fake, on_fallback=lambda: used.append(True))
    print("Offline, limit 8 words:", chain.invoke({"text": base.ARTICLE, "max_words": 8}))
    print(f"  fallback used: {bool(used)}; model calls: {len(fake.received)}")

    # 2. Live: a tight limit, so the fallback may or may not be needed.
    used.clear()
    chain = build_safe_summary_chain(get_chat_model(temperature=0), on_fallback=lambda: used.append(True))
    for limit in (40, 6):
        used.clear()
        summary = chain.invoke({"text": base.ARTICLE, "max_words": limit})
        print(f"\nLive, limit {limit} words ({len(summary.split())} words, fallback used: {bool(used)}):\n  {summary}")


if __name__ == "__main__":
    main()
