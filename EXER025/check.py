"""EXER025 checks. Run:  uv run python EXER025/check.py"""

from langchain_core.embeddings import DeterministicFakeEmbedding
from streamlit.testing.v1 import AppTest

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.rag import KB_DIR

checker = Checker(__file__)
logic = checker.load("docs_logic.py")
FAKE_EMB = DeterministicFakeEmbedding(size=32)


@checker.check("load_uploaded() handles markdown and PDF bytes")
def _():
    md = logic.load_uploaded("shipping.md", (KB_DIR / "shipping.md").read_bytes())
    pdf = logic.load_uploaded("handbook.pdf", (KB_DIR / "employee_handbook.pdf").read_bytes())
    assert md[0].metadata["source"] == "shipping.md"
    assert len(pdf) == 2 and pdf[1].metadata["page"] == 2


@checker.check("load_uploaded() ignores directory tricks in file names")
def _():
    docs = logic.load_uploaded("../../evil.md", b"# hi\nhello")
    assert docs[0].metadata["source"] == "evil.md"


@checker.check("build_index() creates separate in-memory stores")
def _():
    docs = logic.load_uploaded("shipping.md", (KB_DIR / "shipping.md").read_bytes())
    a = logic.build_index(docs, FAKE_EMB)
    b = logic.build_index(docs[:1], FAKE_EMB)
    assert a._collection.count() > 0
    assert a._collection.name != b._collection.name, "each session needs its own collection"


@checker.check("condense_question() makes no LLM call without history")
def _():
    llm = fake_chat_model("SHOULD NOT BE USED")
    assert logic.condense_question(llm, [], "Is shipping free?") == "Is shipping free?"
    assert not llm.received


@checker.check("condense_question() rewrites follow-ups using the history")
def _():
    llm = fake_chat_model("How much does the Cold Brew Bottle cost?")
    history = [{"role": "user", "content": "Tell me about the cold brew bottle"},
               {"role": "assistant", "content": "It's a 1 litre glass bottle."}]
    assert logic.condense_question(llm, history, "How much is it?") == "How much does the Cold Brew Bottle cost?"
    assert any("cold brew bottle" in m.content.lower() for m in llm.received[0])


@checker.check("answer() returns answer, docs and the standalone question")
def _():
    store = logic.build_index(logic.load_uploaded("shipping.md", (KB_DIR / "shipping.md").read_bytes()), FAKE_EMB)
    out = logic.answer(fake_chat_model("Express costs ₱250 [1]."), store, [], "express price?")
    assert out["answer"] == "Express costs ₱250 [1]." and out["docs"] and out["standalone"] == "express price?"


@checker.check("the app starts and asks for documents")
def _():
    at = AppTest.from_file(str(checker.path("app.py")), default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    assert any("Build index" in i.value for i in at.info)


checker.run()
