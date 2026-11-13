"""EXER030 checks. Run:  uv run python EXER030/check.py"""

from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model
from aicourse.rag import NOT_FOUND, get_vector_store

checker = Checker(__file__)
mod = checker.load("agentic_rag.py")

DOCS = [Document(page_content="Pets are welcome at BGC.", metadata={"source": "company_faq.md"}),
        Document(page_content="Shipping is free over 1500.", metadata={"source": "shipping.md"})]
queries = []


def retriever():
    queries.clear()
    return RunnableLambda(lambda q: queries.append(q) or DOCS)


def yes(v=True):
    return mod.RelevanceGrade(relevant=v)


@checker.check("small talk skips retrieval")
def _():
    llm = fake_chat_model("Hello! I'm great.", structured=[mod.RouteDecision(needs_retrieval=False)])
    out = mod.ask(mod.build_graph(llm, retriever()), "Hi!")
    assert out["path"] == ["route", "direct_answer"], out["path"]
    assert not queries, "nothing should be retrieved for small talk"


@checker.check("relevant docs: route -> retrieve -> grade -> generate, irrelevant docs dropped")
def _():
    structured = [mod.RouteDecision(needs_retrieval=True), yes(True), yes(False)]
    llm = fake_chat_model("Yes, pets are welcome at BGC [1].", structured=structured)
    out = mod.ask(mod.build_graph(llm, retriever()), "Can I bring my dog?")
    assert out["path"] == ["route", "retrieve", "grade", "generate"], out["path"]
    assert [d.page_content for d in out["relevant"]] == ["Pets are welcome at BGC."]


@checker.check("nothing relevant -> the query is rewritten and retrieval retried")
def _():
    structured = [mod.RouteDecision(needs_retrieval=True), yes(False), yes(False), yes(True), yes(False)]
    llm = fake_chat_model("refund policy unopened beans", "Returns within 30 days [1].", structured=structured)
    out = mod.ask(mod.build_graph(llm, retriever()), "beans going back")
    assert out["path"] == ["route", "retrieve", "grade", "rewrite", "retrieve", "grade", "generate"], out["path"]
    assert queries == ["beans going back", "refund policy unopened beans"], queries


@checker.check("after MAX_REWRITES failures it falls back honestly")
def _():
    llm = fake_chat_model("another query", structured=[mod.RouteDecision(needs_retrieval=True), yes(False)])
    out = mod.ask(mod.build_graph(llm, retriever()), "GDP of France?")
    assert out["answer"] == NOT_FOUND
    assert out["path"].count("rewrite") == mod.MAX_REWRITES and out["path"][-1] == "fallback", out["path"]


@checker.check("real run: the dog question is answered from company_faq.md  [live API]")
def _():
    graph = mod.build_graph(get_chat_model(temperature=0), get_vector_store().as_retriever(search_kwargs={"k": 4}))
    out = mod.ask(graph, "Can I bring my dog to the café?")
    assert "generate" in out["path"] and "BGC" in out["answer"], (out["path"], out["answer"])


checker.run()
