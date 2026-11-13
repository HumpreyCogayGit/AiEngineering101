"""EXER030 — Agentic RAG (reference solution).

Plain RAG always retrieves once and always answers. Agentic RAG makes
decisions along the way:
  - Does this question need the documents at all?       (route)
  - Are the retrieved chunks actually relevant?         (grade)
  - If not, can a better search query fix it?           (rewrite + retry)
  - If nothing works, say so honestly.                  (fallback)
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from aicourse.llm import get_chat_model
from aicourse.rag import NOT_FOUND, RAG_SYSTEM_PROMPT, format_docs, get_vector_store

MAX_REWRITES = 2


class RAGState(TypedDict, total=False):
    question: str            # what the user asked
    query: str               # what we search for (may be rewritten)
    docs: list[Document]     # retrieved
    relevant: list[Document]  # retrieved AND graded relevant
    answer: str
    rewrites: int
    path: list[str]          # for debugging: which nodes ran


class RouteDecision(BaseModel):
    needs_retrieval: bool = Field(
        description="True for ANY question that asks for information, even when it looks unrelated "
                    "to coffee: the documents decide whether we can answer it. "
                    "False ONLY for greetings, thanks and small talk."
    )


class RelevanceGrade(BaseModel):
    relevant: bool = Field(description="True if the passage helps answer the question")


def build_graph(llm: BaseChatModel, retriever: Runnable):
    router = llm.with_structured_output(RouteDecision)
    grader = llm.with_structured_output(RelevanceGrade)
    answer_chain = ChatPromptTemplate.from_messages(
        [("system", RAG_SYSTEM_PROMPT), ("human", "{question}")]) | llm | StrOutputParser()

    def route_question(state: RAGState) -> dict:
        return {"query": state["question"], "rewrites": 0, "path": ["route"]}

    def decide(state: RAGState) -> Literal["retrieve", "direct_answer"]:
        decision = router.invoke(f"Question: {state['question']}")
        return "retrieve" if decision.needs_retrieval else "direct_answer"

    def retrieve(state: RAGState) -> dict:
        return {"docs": retriever.invoke(state["query"]), "path": state["path"] + ["retrieve"]}

    def grade(state: RAGState) -> dict:
        relevant = [
            d for d in state["docs"]
            if grader.invoke(f"Question: {state['question']}\n\nPassage:\n{d.page_content}").relevant
        ]
        return {"relevant": relevant, "path": state["path"] + ["grade"]}

    def after_grade(state: RAGState) -> Literal["generate", "rewrite", "fallback"]:
        if state["relevant"]:
            return "generate"
        return "rewrite" if state["rewrites"] < MAX_REWRITES else "fallback"

    def rewrite(state: RAGState) -> dict:
        better = llm.invoke(
            "The search query below found nothing useful in a coffee company's knowledge base "
            "(products, refunds, shipping, brewing, loyalty, stores, jobs, HR). "
            f"Write ONE better search query. Output only the query.\n\nQuestion: {state['question']}\n"
            f"Previous query: {state['query']}"
        ).text.strip()
        return {"query": better, "rewrites": state["rewrites"] + 1, "path": state["path"] + ["rewrite"]}

    def generate(state: RAGState) -> dict:
        answer = answer_chain.invoke({"context": format_docs(state["relevant"]), "question": state["question"]})
        return {"answer": answer, "path": state["path"] + ["generate"]}

    def direct_answer(state: RAGState) -> dict:
        # Small talk only: this node has no documents, so it must not answer factual questions.
        reply = llm.invoke([
            SystemMessage("You are the friendly Nimbus Coffee assistant. The user is making small talk: "
                          "reply in one short, warm sentence and offer help with Nimbus Coffee questions. "
                          "Do not state facts from your own knowledge."),
            HumanMessage(state["question"]),
        ])
        return {"answer": reply.text, "path": state["path"] + ["direct_answer"]}

    def fallback(state: RAGState) -> dict:
        return {"answer": NOT_FOUND, "path": state["path"] + ["fallback"]}

    builder = StateGraph(RAGState)
    for name, fn in [("route", route_question), ("retrieve", retrieve), ("grade", grade), ("rewrite", rewrite),
                     ("generate", generate), ("direct_answer", direct_answer), ("fallback", fallback)]:
        builder.add_node(name, fn)
    builder.add_edge(START, "route")
    builder.add_conditional_edges("route", decide, ["retrieve", "direct_answer"])
    builder.add_edge("retrieve", "grade")
    builder.add_conditional_edges("grade", after_grade, ["generate", "rewrite", "fallback"])
    builder.add_edge("rewrite", "retrieve")
    for end_node in ("generate", "direct_answer", "fallback"):
        builder.add_edge(end_node, END)
    return builder.compile()


def ask(graph, question: str) -> dict:
    return graph.invoke({"question": question})


def main() -> None:
    graph = build_graph(get_chat_model(temperature=0), get_vector_store().as_retriever(search_kwargs={"k": 4}))
    print(graph.get_graph().draw_mermaid())
    for q in ["Hi there! How are you?", "Can I bring my dog to the café?",
              "something about beans going back", "What is the GDP of France?"]:
        result = ask(graph, q)
        print(f"\nQ: {q}\n   path: {' -> '.join(result['path'])}\nA: {result['answer']}")


if __name__ == "__main__":
    main()
