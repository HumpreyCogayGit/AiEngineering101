"""EXER020 — Loading and Chunking.

RAG step 1: turn files of many formats into clean text Documents with
metadata, then split them into chunks small enough to embed and retrieve
precisely, but big enough to keep their meaning.

    uv run python EXER020/starter/ingest.py
    uv run python EXER020/check.py
"""

from __future__ import annotations

import re
import statistics
from pathlib import Path

from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from aicourse.settings import DATA_DIR

KB_DIR = DATA_DIR / "knowledge_base"


def load_text(path: Path) -> list[Document]:
    """Markdown / plain text: ONE Document for the whole file, metadata {"source": path.name}."""
    # TODO
    raise NotImplementedError("load_text")


def load_html(path: Path) -> list[Document]:
    """Keep the readable text; drop scripts, styles, navigation and footers.

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]): tag.decompose()
    text = soup.get_text("\n"), then collapse runs of blank lines:
        re.sub(r"\n\s*\n+", "\n\n", text).strip()
    metadata: {"source": path.name, "title": <the <title> text>}
    """
    # TODO
    raise NotImplementedError("load_html")


def load_pdf(path: Path) -> list[Document]:
    """One Document PER PAGE: PdfReader(str(path)).pages, page.extract_text().
    metadata: {"source": path.name, "page": <1-based page number>}"""
    # TODO
    raise NotImplementedError("load_pdf")


LOADERS = {".md": load_text, ".txt": load_text, ".html": load_html, ".htm": load_html, ".pdf": load_pdf}


def load_directory(directory: Path) -> list[Document]:
    """Load every supported file (sorted by name) using LOADERS; skip empty documents."""
    # TODO
    raise NotImplementedError("load_directory")


def chunk_documents(docs: list[Document], chunk_size: int = 600, chunk_overlap: int = 100) -> list[Document]:
    """Split with RecursiveCharacterTextSplitter.

    separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " ", ""] — try headings first,
    then paragraphs, lines, sentences, words.
    splitter.split_documents(docs) keeps each chunk's metadata (source, page).
    Then add metadata["chunk_id"] = 0, 1, 2, ... to every chunk.
    """
    # TODO
    raise NotImplementedError("chunk_documents")


def chunk_stats(chunks: list[Document]) -> dict:
    sizes = [len(c.page_content) for c in chunks]
    return {
        "count": len(sizes),
        "min": min(sizes),
        "max": max(sizes),
        "mean": round(statistics.mean(sizes), 1),
        "sources": len({c.metadata["source"] for c in chunks}),
    }


def main() -> None:
    docs = load_directory(KB_DIR)
    print(f"Loaded {len(docs)} documents:")
    for d in docs:
        print(f"  {d.metadata['source']:<24} {len(d.page_content):>5} chars  {d.metadata}")

    print("\nHTML after cleaning (no nav, no script):")
    print("  ", load_html(KB_DIR / "careers.html")[0].page_content[:160].replace("\n", " | "))

    for size, overlap in [(200, 0), (600, 100), (1500, 200)]:
        chunks = chunk_documents(docs, size, overlap)
        print(f"\nchunk_size={size}, overlap={overlap}: {chunk_stats(chunks)}")
    sample = chunk_documents(docs, 600, 100)[3]
    print("\nA sample chunk:\n", sample.metadata, "\n", sample.page_content)


if __name__ == "__main__":
    main()
