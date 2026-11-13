"""EXER023 checks. Run:  uv run python EXER023/check.py"""

import json

from langchain_core.documents import Document

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.rag import load_knowledge_base, split_documents
from aicourse.settings import DATA_DIR

checker = Checker(__file__)
mod = checker.load("better_retrieval.py")
CHUNKS = split_documents(load_knowledge_base())


def doc(text, source="x.md"):
    return Document(page_content=text, metadata={"source": source})


A, B, C, D = doc("alpha"), doc("bravo"), doc("charlie"), doc("delta")


@checker.check("BM25 finds exact rare terms (e.g. 'Liberica')")
def _():
    results = mod.BM25Retriever(CHUNKS).search("Liberica", k=1)
    assert len(results) == 1 and "Liberica" in results[0].page_content, results


@checker.check("BM25 search returns k results, best first")
def _():
    results = mod.BM25Retriever(CHUNKS).search("cold brew steep hours fridge", k=3)
    assert len(results) == 3 and results[0].metadata["source"] == "brewing_guide.md"


@checker.check("reciprocal_rank_fusion() rewards documents ranked high in several lists")
def _():
    fused = mod.reciprocal_rank_fusion([[A, B, C], [B, D, A]])
    assert [d.page_content for d in fused][:2] == ["bravo", "alpha"], [d.page_content for d in fused]
    assert len(fused) == 4, "each document must appear once"


@checker.check("reciprocal_rank_fusion() uses 1/(k+rank)")
def _():
    fused = mod.reciprocal_rank_fusion([[A, B], [C]], k=1)
    # A: 1/2, C: 1/2, B: 1/3  -> B must be last
    assert fused[-1].page_content == "bravo"


@checker.check("hit_rate() counts expected sources in the top k and skips null rows")
def _():
    data = [{"question": "q1", "expected_source": "a.md"},
            {"question": "q2", "expected_source": "b.md"},
            {"question": "q3", "expected_source": None}]
    retrieve = lambda q: [doc("x", "a.md"), doc("y", "c.md")]
    assert mod.hit_rate(retrieve, data, k=2) == 0.5
    assert mod.hit_rate(lambda q: [doc("y", "c.md"), doc("x", "a.md")], data, k=1) == 0.0


@checker.check("multi_query() returns the original plus the rephrasings")
def _():
    llm = fake_chat_model(structured=[mod.Queries(queries=["refund timeline", "return window", "money back days"])])
    out = mod.multi_query(llm, "How long to get my money back?", n=3)
    assert out[0] == "How long to get my money back?" and len(out) == 4, out


@checker.check("hybrid retrieval beats or ties plain vector search  [live API]")
def _():
    dataset = json.loads((DATA_DIR / "eval_questions.json").read_text())
    retrievers = mod.build_retrievers()
    vector, hybrid = mod.hit_rate(retrievers["vector"], dataset), mod.hit_rate(retrievers["hybrid"], dataset)
    print(f"         vector={vector:.0%} hybrid={hybrid:.0%}")
    assert hybrid >= vector and hybrid >= 0.8


checker.run()
