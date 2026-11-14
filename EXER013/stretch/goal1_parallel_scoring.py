"""EXER013 stretch goal 1 — score the translation in a parallel branch.

    uv run python EXER013/stretch/goal1_parallel_scoring.py

After the translation, two things are computed from the same input:
a back-translation into English and a 1-5 faithfulness score. Neither needs
the other, so they are branches, not steps. `assign` with two keys runs them
in parallel (it is a RunnableParallel underneath) and merges both results.

    {text, ...} -> +summary -> +translation -> +score          (parallel)
                                               +back_translation
"""

from __future__ import annotations

import time

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "chains.py")

score_prompt = ChatPromptTemplate.from_messages([
    ("system", "You grade translations. Reply with one digit from 1 to 5 and nothing else. "
               "5 = says exactly what the original says, 1 = different meaning."),
    ("human", "Original:\n{summary}\n\nTranslation into {language}:\n{translation}"),
])
back_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional translator. Output only the translation."),
    ("human", "Translate into English:\n\n{translation}"),
])


def to_score(text: str) -> int | None:
    digits = [c for c in text if c.isdigit()]
    return int(digits[0]) if digits and 1 <= int(digits[0]) <= 5 else None


def build_scored_pipeline(llm) -> Runnable:
    parser = StrOutputParser()
    return base.build_pipeline(llm) | RunnablePassthrough.assign(
        score=score_prompt | llm | parser | to_score,           # branch 1
        back_translation=back_prompt | llm | parser,            # branch 2, at the same time
    )


def main() -> None:
    pipeline = build_scored_pipeline(get_chat_model(temperature=0))
    start = time.perf_counter()
    result = pipeline.invoke({"text": base.ARTICLE, "max_words": 30, "language": "Filipino"})
    print(f"Keys: {list(result)}  ({time.perf_counter() - start:.1f}s for 4 model calls, 2 of them in parallel)")
    print("\nSummary         :", result["summary"])
    print("Translation     :", result["translation"])
    print("Back-translation:", result["back_translation"])
    print("Score           :", result["score"], "/ 5")


if __name__ == "__main__":
    main()
