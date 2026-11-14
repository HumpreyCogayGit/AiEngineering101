"""EXER030 stretch goal 1 — check the answer for hallucinations before returning it.

    uv run python EXER030/stretch/goal1_hallucination_check.py

The exercise grades the DOCUMENTS. Nothing yet checks the ANSWER: a model can
still add a fact that is in none of the relevant chunks. One more node does
it: a grader reads the answer and the chunks it was built from, and says
whether every claim is supported. An unsupported answer is replaced by the
honest fallback, never shown.

The existing graph is used unchanged, as a single node of a larger graph:

    START -> rag (the whole EXER030 graph) -> verify --grounded--> END
                                                |
                                                +--not grounded--> fallback -> END
"""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model
from aicourse.rag import NOT_FOUND, format_docs, get_vector_store
from aicourse.stretch import solution_module

base = solution_module(__file__, "agentic_rag.py")


class Grounding(BaseModel):
    unsupported: list[str] = Field(description="Claims in the answer that the passages do NOT support. "
                                               "Empty when every claim is supported.")
    grounded: bool = Field(description="True only if the list of unsupported claims is empty")


class CheckedState(base.RAGState, total=False):
    grounded: bool
    unsupported: list[str]


def build_checked_graph(llm, retriever, rag_graph=None):
    rag_graph = rag_graph or base.build_graph(llm, retriever)
    checker = llm.with_structured_output(Grounding)

    def verify(state: CheckedState) -> dict:
        if state["path"][-1] != "generate":  # small talk and the fallback make no claims from documents
            return {"grounded": True, "unsupported": [], "path": state["path"] + ["verify"]}
        verdict = checker.invoke(
            "Check the answer against the passages. List every claim the passages do not support.\n\n"
            f"Passages:\n{format_docs(state['relevant'])}\n\nAnswer:\n{state['answer']}"
        )
        return {"grounded": verdict.grounded and not verdict.unsupported,
                "unsupported": verdict.unsupported, "path": state["path"] + ["verify"]}

    def after_verify(state: CheckedState) -> Literal["fallback", "__end__"]:
        return END if state["grounded"] else "fallback"

    def fallback(state: CheckedState) -> dict:
        return {"answer": NOT_FOUND, "path": state["path"] + ["fallback"]}

    builder = StateGraph(CheckedState)
    builder.add_node("rag", rag_graph)  # a compiled graph is a valid node
    builder.add_node("verify", verify)
    builder.add_node("fallback", fallback)
    builder.add_edge(START, "rag")
    builder.add_edge("rag", "verify")
    builder.add_conditional_edges("verify", after_verify, ["fallback", END])
    builder.add_edge("fallback", END)
    return builder.compile()


def main() -> None:
    llm = get_chat_model(temperature=0)
    retriever = get_vector_store().as_retriever(search_kwargs={"k": 4})

    print("1. Live: an honest answer passes the check.")
    result = build_checked_graph(llm, retriever).invoke({"question": "Can I bring my dog to the café?"})
    print(f"   path: {' -> '.join(result['path'])}\n   A: {result['answer']}")

    print("\n2. A dishonest generator: the RAG graph is scripted to invent a fact; the real model checks it.")
    liar = fake_chat_model(
        "Dogs are welcome at every Nimbus café, and each dog gets a free puppuccino. [1]",
        structured=[base.RouteDecision(needs_retrieval=True), base.RelevanceGrade(relevant=True)],
    )
    rag_that_lies = base.build_graph(liar, retriever)
    result = build_checked_graph(llm, retriever, rag_graph=rag_that_lies).invoke(
        {"question": "Can I bring my dog to the café?"})
    print(f"   path: {' -> '.join(result['path'])}")
    print(f"   unsupported claims found: {result['unsupported']}")
    print(f"   A: {result['answer']}")


if __name__ == "__main__":
    main()
