"""EXER022 — The RAG Chain (reference solution).

Retrieval-Augmented Generation = retrieve relevant chunks, put them in the
prompt, and instruct the model to answer ONLY from them, with citations.
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

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are the customer assistant of Nimbus Coffee Co.\n"
     "Answer the question using ONLY the numbered context passages below.\n"
     "Rules:\n"
     "- Cite the passages you used with their number in square brackets, e.g. [1] or [2][3].\n"
     f"- If the answer is not in the context, reply exactly: {NOT_FOUND}\n"
     "- Never use outside knowledge. Be concise.\n\n"
     "Context:\n{context}"),
    ("human", "{question}"),
])


def format_docs(docs: list[Document]) -> str:
    """[1] (source: refund_policy.md)\n<text>\n\n[2] (source: ...)"""
    return "\n\n".join(
        f"[{i}] (source: {d.metadata.get('source', '?')})\n{d.page_content}"
        for i, d in enumerate(docs, start=1)
    )


def build_rag_chain(retriever: Runnable, llm: BaseChatModel) -> Runnable:
    """question (str) -> {"question", "docs", "answer"}"""
    generate = (
        RunnableLambda(lambda x: {"context": format_docs(x["docs"]), "question": x["question"]})
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    return (
        RunnableParallel(docs=retriever, question=RunnablePassthrough())
        | RunnablePassthrough.assign(answer=generate)
    )


def cited_sources(answer: str, docs: list[Document]) -> list[str]:
    """Map the [n] markers in the answer back to source file names (unique, in order)."""
    sources: list[str] = []
    for number in re.findall(r"\[(\d+)\]", answer):
        index = int(number) - 1
        if 0 <= index < len(docs):
            source = docs[index].metadata.get("source", "?")
            if source not in sources:
                sources.append(source)
    return sources


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
