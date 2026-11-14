"""EXER022 stretch goal 1 — the exact quoted sentence behind each citation.

    uv run python EXER022/stretch/goal1_quoted_citations.py

"[1]" says which passage. A quote says which SENTENCE, and a quote can be
checked by code: it either appears in the passage, word for word, or it does
not. The model returns structured output (answer + citations), and
`verify()` confirms every quote against the retrieved text. A quote that is
not found means the model paraphrased or invented: flag it.
"""

from __future__ import annotations

import re

from langchain_core.documents import Document
from pydantic import BaseModel, Field

from aicourse.llm import get_chat_model
from aicourse.rag import get_vector_store
from aicourse.stretch import solution_module

base = solution_module(__file__, "rag_chain.py")

SYSTEM = (
    "You are the customer assistant of Nimbus Coffee Co.\n"
    "Answer the question using ONLY the numbered context passages below.\n"
    "For every passage you use, give one citation: the passage number and a quote.\n"
    "The quote must be copied character for character from that passage (one sentence or less), "
    "including any ** marks. Do not paraphrase a quote.\n"
    f"If the answer is not in the context, set answer to exactly: {base.NOT_FOUND} and give no citations.\n\n"
    "Context:\n{context}"
)


class Citation(BaseModel):
    passage: int = Field(description="Number of the passage, as shown in square brackets")
    quote: str = Field(description="Text copied exactly from that passage that supports the answer")


class CitedAnswer(BaseModel):
    answer: str = Field(description="The answer, concise")
    citations: list[Citation] = Field(description="One entry per passage used; empty if the answer is unknown")


def squash(text: str) -> str:
    """Line breaks inside a passage must not make an exact quote fail."""
    return re.sub(r"\s+", " ", text).strip()


def verify(citation: Citation, docs: list[Document]) -> bool:
    if not 1 <= citation.passage <= len(docs):
        return False
    return squash(citation.quote) in squash(docs[citation.passage - 1].page_content)


def answer_with_quotes(retriever, llm, question: str) -> tuple[CitedAnswer, list[Document]]:
    docs = retriever.invoke(question)
    result = llm.with_structured_output(CitedAnswer).invoke(
        [("system", SYSTEM.format(context=base.format_docs(docs))), ("human", question)]
    )
    return result, docs


def main() -> None:
    retriever = get_vector_store().as_retriever(search_kwargs={"k": 4})
    llm = get_chat_model(temperature=0)
    for question in ["How long do I have to return unopened beans?",
                     "Is shipping free, and how fast is express delivery in Metro Manila?",
                     "What is the capital of Peru?"]:
        result, docs = answer_with_quotes(retriever, llm, question)
        print(f"\nQ: {question}\nA: {result.answer}")
        for c in result.citations:
            source = docs[c.passage - 1].metadata["source"] if 1 <= c.passage <= len(docs) else "?"
            print(f"   [{c.passage}] {source}: \"{c.quote}\"  {'verified' if verify(c, docs) else 'NOT FOUND IN PASSAGE'}")


if __name__ == "__main__":
    main()
