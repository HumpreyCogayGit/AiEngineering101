"""EXER022 checks. Run:  uv run python EXER022/check.py"""

from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model
from aicourse.rag import get_vector_store

checker = Checker(__file__)
mod = checker.load("rag_chain.py")

DOCS = [
    Document(page_content="Shipping is free over 1500.", metadata={"source": "shipping.md"}),
    Document(page_content="Returns within 30 days.", metadata={"source": "refund_policy.md"}),
]
fake_retriever = RunnableLambda(lambda question: DOCS)


@checker.check("RAG_PROMPT has {context} and {question} and the NOT_FOUND rule")
def _():
    if mod.RAG_PROMPT is None:
        raise NotImplementedError("RAG_PROMPT")
    assert set(mod.RAG_PROMPT.input_variables) == {"context", "question"}, mod.RAG_PROMPT.input_variables
    system_text = mod.RAG_PROMPT.messages[0].prompt.template
    assert mod.NOT_FOUND in system_text, "tell the model exactly what to say when the answer is missing"


@checker.check("format_docs() numbers passages and names their sources")
def _():
    text = mod.format_docs(DOCS)
    assert text.startswith("[1] (source: shipping.md)"), text[:40]
    assert "[2] (source: refund_policy.md)" in text and "Returns within 30 days." in text


@checker.check("build_rag_chain() returns question, docs and answer")
def _():
    llm = fake_chat_model("Returns are accepted for 30 days [2].")
    out = mod.build_rag_chain(fake_retriever, llm).invoke("How long for returns?")
    assert out["question"] == "How long for returns?"
    assert out["docs"] == DOCS
    assert out["answer"] == "Returns are accepted for 30 days [2]."


@checker.check("the model receives the retrieved context and the question")
def _():
    llm = fake_chat_model("ok")
    mod.build_rag_chain(fake_retriever, llm).invoke("How long for returns?")
    sent = "\n".join(m.content for m in llm.received[0])
    assert "Returns within 30 days." in sent and "How long for returns?" in sent


@checker.check("cited_sources() maps [n] to unique source names")
def _():
    assert mod.cited_sources("A [2]. B [1][2]. C [9].", DOCS) == ["refund_policy.md", "shipping.md"]
    assert mod.cited_sources("no citations", DOCS) == []


@checker.check("answers a policy question with a citation  [live API]")
def _():
    chain = mod.build_rag_chain(get_vector_store().as_retriever(search_kwargs={"k": 4}), get_chat_model(temperature=0))
    out = chain.invoke("How many days do I have to return unopened coffee beans?")
    assert "30" in out["answer"], out["answer"]
    assert "refund_policy.md" in mod.cited_sources(out["answer"], out["docs"]), out["answer"]


@checker.check("refuses to answer an out-of-scope question  [live API]")
def _():
    chain = mod.build_rag_chain(get_vector_store().as_retriever(search_kwargs={"k": 4}), get_chat_model(temperature=0))
    out = chain.invoke("What is the price of a Tesla Model 3?")
    assert "don't know" in out["answer"].lower(), out["answer"]


checker.run()
