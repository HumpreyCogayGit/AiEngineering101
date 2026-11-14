"""EXER022 stretch goal 2 — stream the answer, then print the sources (EXER007).

    uv run python EXER022/stretch/goal2_stream_with_sources.py

The exercise's chain returns everything at once. To stream, split it at the
natural seam: retrieval finishes first (it is fast and the sources are known
immediately), then the generation step streams. The sources are printed at
the end because the citations are only complete when the answer is.
"""

from __future__ import annotations

import time

from langchain_core.output_parsers import StrOutputParser

from aicourse.llm import get_chat_model
from aicourse.rag import get_vector_store
from aicourse.stretch import solution_module

base = solution_module(__file__, "rag_chain.py")


def stream_answer(retriever, llm, question: str, on_token=print) -> dict:
    """Like the RAG chain, but the answer arrives piece by piece through on_token."""
    start = time.perf_counter()
    docs = retriever.invoke(question)                       # 1. retrieve (not streamed)
    retrieved_after = time.perf_counter() - start
    generate = base.RAG_PROMPT | llm | StrOutputParser()    # 2. the generation half of the chain
    parts: list[str] = []
    first_token_after = None
    for piece in generate.stream({"context": base.format_docs(docs), "question": question}):
        if first_token_after is None:
            first_token_after = time.perf_counter() - start
        parts.append(piece)
        on_token(piece)
    answer = "".join(parts)
    return {"question": question, "docs": docs, "answer": answer,
            "sources": base.cited_sources(answer, docs),    # 3. sources, once the answer is complete
            "timing": {"retrieved": retrieved_after, "first_token": first_token_after,
                       "total": time.perf_counter() - start}}


def main() -> None:
    retriever = get_vector_store().as_retriever(search_kwargs={"k": 4})
    llm = get_chat_model(temperature=0)
    for question in ["My order arrived broken. What should I do?", "What is the capital of Peru?"]:
        print(f"\nQ: {question}\nA: ", end="")
        result = stream_answer(retriever, llm, question, on_token=lambda piece: print(piece, end="", flush=True))
        t = result["timing"]
        print(f"\n   sources: {', '.join(result['sources']) or 'none'}")
        print(f"   retrieved after {t['retrieved']:.2f}s, first token after {t['first_token']:.2f}s, "
              f"done after {t['total']:.2f}s")


if __name__ == "__main__":
    main()
