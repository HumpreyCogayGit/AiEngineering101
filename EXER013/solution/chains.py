"""EXER013 — Prompts and Chains (reference solution).

Prompt templates + models + output parsers are all *Runnables*. The pipe
operator `|` (LCEL) connects them into a chain, which is itself a Runnable
with invoke / stream / batch.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough

from aicourse.llm import get_chat_model

ARTICLE = """The city council approved a plan on Tuesday to convert three downtown parking
garages into mixed-use buildings with affordable apartments, ground-floor shops and
rooftop gardens. Supporters say the project will add 600 homes and revive the evening
economy, while some business owners worry about losing customer parking. Construction
is expected to start next spring and take about two years. The council also promised
to expand the free shuttle bus to cover the area before the garages close."""

summary_prompt = ChatPromptTemplate.from_messages([
    ("system", "You summarize news articles accurately and neutrally."),
    ("human", "Summarize the following article in at most {max_words} words:\n\n{text}"),
])

translate_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional translator. Output only the translation."),
    ("human", "Translate into {language}:\n\n{summary}"),
])


def build_summary_chain(llm: BaseChatModel) -> Runnable:
    """{text, max_words} -> summary string"""
    return summary_prompt | llm | StrOutputParser()


def build_translate_chain(llm: BaseChatModel) -> Runnable:
    """{summary, language} -> translation string"""
    return translate_prompt | llm | StrOutputParser()


def build_pipeline(llm: BaseChatModel) -> Runnable:
    """{text, max_words, language} -> {text, max_words, language, summary, translation}

    RunnablePassthrough.assign keeps the input keys and ADDS a new key computed
    from them, so the second step can use the first step's output.
    """
    return (
        RunnablePassthrough.assign(summary=build_summary_chain(llm))
        | RunnablePassthrough.assign(translation=build_translate_chain(llm))
    )


def main() -> None:
    llm = get_chat_model(temperature=0)

    print("The prompt template expects:", summary_prompt.input_variables)
    print("\nFilled-in prompt:\n", summary_prompt.invoke({"text": "TEXT", "max_words": 20}).to_messages())

    summary = build_summary_chain(llm).invoke({"text": ARTICLE, "max_words": 40})
    print("\nSummary:", summary)

    result = build_pipeline(llm).invoke({"text": ARTICLE, "max_words": 40, "language": "Filipino"})
    print("\nTranslation:", result["translation"])

    print("\nBatch translate into 3 languages:")
    outs = build_translate_chain(llm).batch(
        [{"summary": summary, "language": lang} for lang in ("Spanish", "Japanese", "German")]
    )
    for o in outs:
        print(" -", o[:100])


if __name__ == "__main__":
    main()
