"""EXER022 — The RAG Chain.

Retrieval-Augmented Generation = retrieve relevant chunks, put them in the
prompt, and instruct the model to answer ONLY from them, with citations.

`aicourse.rag.get_vector_store()` gives you the Chroma index of the knowledge
base (what you built in EXER020-021), creating it on first use.

    uv run python EXER022/starter/rag_chain.py
    uv run python EXER022/check.py
"""

from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda, RunnableParallel, RunnablePassthrough

from aicourse.llm import get_chat_model
from aicourse.rag import get_vector_store

NOT_FOUND = "I don't know based on the available documents."

# TODO: write the grounding prompt. The system message must:
#   - say the assistant works for Nimbus Coffee Co.
#   - say to answer ONLY from the numbered context passages
#   - require citations like [1] or [2][3]
#   - say that if the answer is not in the context, reply exactly NOT_FOUND
#   - contain the {context} variable
# The human message is just {question}.
RAG_PROMPT: ChatPromptTemplate | None = None


def format_docs(docs: list[Document]) -> str:
    """Number the passages so the model can cite them:

    [1] (source: refund_policy.md)
    <chunk text>

    [2] (source: shipping.md)
    <chunk text>
    """
    # TODO
    raise NotImplementedError("format_docs")


def build_rag_chain(retriever: Runnable, llm: BaseChatModel) -> Runnable:
    """question (str) -> {"question": str, "docs": list[Document], "answer": str}

    Hint:
        generate = RunnableLambda(lambda x: {"context": format_docs(x["docs"]), "question": x["question"]})
                   | RAG_PROMPT | llm | StrOutputParser()
        return RunnableParallel(docs=retriever, question=RunnablePassthrough())
               | RunnablePassthrough.assign(answer=generate)
    Returning the docs as well as the answer lets the UI show sources.
    """
    # TODO
    raise NotImplementedError("build_rag_chain")


def cited_sources(answer: str, docs: list[Document]) -> list[str]:
    """Map the [n] markers in the answer back to source file names.

    "Returns take 30 days [2]." with docs[1] from refund_policy.md -> ["refund_policy.md"]
    Unique, in order of first citation; ignore numbers that are out of range.
    """
    # TODO
    raise NotImplementedError("cited_sources")


def main() -> None:
    retriever = get_vector_store().as_retriever(search_kwargs={"k": 4})
    chain = build_rag_chain(retriever, get_chat_model(temperature=0))
    print("Ask Nimbus Coffee anything (empty line to quit).")
    for example in ["How long do I have to return unopened beans?", "What is the capital of Peru?"]:
        print(f"  e.g. {example}")
    while True:
        try:
            question = input("\nQ: ").strip()
        except (EOFError, KeyboardInterrupt):  # Ctrl-D / Ctrl-C end the session quietly
            break
        if not question:
            break
        result = chain.invoke(question)
        print("A:", result["answer"])
        print("   sources:", ", ".join(cited_sources(result["answer"], result["docs"])) or "none")


if __name__ == "__main__":
    main()
