"""EXER021 checks. Run:  uv run python EXER021/check.py

Most checks use a fake (deterministic, offline) embedding model in a temp folder.
"""

import tempfile

from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from aicourse.check import Checker
from aicourse.llm import get_embeddings
from aicourse.rag import load_knowledge_base, split_documents

checker = Checker(__file__)
mod = checker.load("vector_store.py")
FAKE = DeterministicFakeEmbedding(size=32)
CHUNKS = split_documents(load_knowledge_base())


@checker.check("make_id() is deterministic and content-based")
def _():
    a = Document(page_content="hello", metadata={"source": "a.md"})
    b = Document(page_content="hello", metadata={"source": "a.md"})
    c = Document(page_content="hello!", metadata={"source": "a.md"})
    assert mod.make_id(a) == mod.make_id(b) != mod.make_id(c)
    assert len(mod.make_id(a)) == 32


@checker.check("add_chunks() stores every chunk")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        store = mod.open_store(tmp, FAKE, "test1")
        assert mod.add_chunks(store, CHUNKS) == len(CHUNKS)
        assert mod.count(store) == len(CHUNKS)


@checker.check("add_chunks() is idempotent (no duplicates on re-run)")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        store = mod.open_store(tmp, FAKE, "test2")
        mod.add_chunks(store, CHUNKS)
        assert mod.add_chunks(store, CHUNKS) == 0
        assert mod.count(store) == len(CHUNKS)


@checker.check("data persists: a new client on the same folder sees the chunks")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        mod.add_chunks(mod.open_store(tmp, FAKE, "test3"), CHUNKS[:5])
        assert mod.count(mod.open_store(tmp, FAKE, "test3")) == 5


@checker.check("search() returns k (Document, score) pairs and supports a source filter")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        store = mod.open_store(tmp, FAKE, "test4")
        mod.add_chunks(store, CHUNKS)
        results = mod.search(store, "anything", k=3)
        assert len(results) == 3 and isinstance(results[0][0], Document)
        filtered = mod.search(store, "anything", k=3, source="shipping.md")
        assert filtered and all(d.metadata["source"] == "shipping.md" for d, _ in filtered)


@checker.check("real embeddings find the pets answer in company_faq.md  [live API]")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        store = mod.open_store(tmp, get_embeddings(), "live")
        mod.add_chunks(store, CHUNKS)
        doc, _ = mod.search(store, "Can I bring my dog?", k=1)[0]
        assert doc.metadata["source"] == "company_faq.md", doc.metadata


checker.run()
