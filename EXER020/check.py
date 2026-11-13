"""EXER020 checks (offline). Run:  uv run python EXER020/check.py"""

from langchain_core.documents import Document

from aicourse.check import Checker
from aicourse.settings import DATA_DIR

checker = Checker(__file__)
mod = checker.load("ingest.py")
KB = DATA_DIR / "knowledge_base"


@checker.check("load_text() returns one Document with the file name as source")
def _():
    docs = mod.load_text(KB / "shipping.md")
    assert len(docs) == 1 and isinstance(docs[0], Document)
    assert docs[0].metadata["source"] == "shipping.md"
    assert "Metro Manila" in docs[0].page_content


@checker.check("load_html() keeps content and drops <script>, <nav> and <footer>")
def _():
    doc = mod.load_html(KB / "careers.html")[0]
    text = doc.page_content
    assert "Barista Academy" in text
    assert "analytics" not in text, "script content leaked into the text"
    assert "Shop" not in text, "navigation leaked into the text"
    assert "©" not in text, "footer leaked into the text"
    assert doc.metadata.get("title") == "Careers at Nimbus Coffee Co."


@checker.check("load_pdf() returns one Document per page with page numbers")
def _():
    docs = mod.load_pdf(KB / "employee_handbook.pdf")
    assert [d.metadata["page"] for d in docs] == [1, 2]
    assert "vacation" in docs[0].page_content and "training budget" in docs[1].page_content


@checker.check("load_directory() loads all 9 documents (7 files, PDF has 2 pages)")
def _():
    docs = mod.load_directory(KB)
    assert len(docs) == 9, len(docs)
    assert len({d.metadata["source"] for d in docs}) == 8


@checker.check("chunk_documents() respects chunk_size and keeps metadata")
def _():
    chunks = mod.chunk_documents(mod.load_directory(KB), chunk_size=300, chunk_overlap=50)
    assert all(len(c.page_content) <= 300 for c in chunks), max(len(c.page_content) for c in chunks)
    assert all("source" in c.metadata for c in chunks)
    pdf_chunks = [c for c in chunks if c.metadata["source"].endswith(".pdf")]
    assert pdf_chunks and all("page" in c.metadata for c in pdf_chunks), "PDF chunks lost their page number"


@checker.check("chunk_documents() numbers chunks with chunk_id")
def _():
    chunks = mod.chunk_documents(mod.load_directory(KB))
    assert [c.metadata["chunk_id"] for c in chunks] == list(range(len(chunks)))


@checker.check("smaller chunk_size produces more chunks; overlap repeats text")
def _():
    docs = mod.load_directory(KB)
    assert len(mod.chunk_documents(docs, 200, 0)) > len(mod.chunk_documents(docs, 1000, 0))
    doc = [Document(page_content=" ".join(f"word{i}" for i in range(300)), metadata={"source": "x"})]
    a, b = mod.chunk_documents(doc, 200, 60)[:2]
    assert a.page_content.split()[-1] in b.page_content, "with overlap, chunk 2 should repeat the end of chunk 1"


checker.run()
