"""EXER020 — Loading and Chunking (reference solution).

RAG step 1: turn files of many formats into clean text Documents with
metadata, then split them into chunks small enough to embed and retrieve
precisely, but big enough to keep their meaning.
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
    """Markdown / plain text: one Document for the whole file."""
    return [Document(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name})]


def load_html(path: Path) -> list[Document]:
    """Keep the readable text; drop scripts, styles, navigation and footers."""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    text = re.sub(r"\n\s*\n+", "\n\n", soup.get_text("\n")).strip()
    title = soup.title.get_text(strip=True) if soup.title else path.stem
    return [Document(page_content=text, metadata={"source": path.name, "title": title})]


def load_pdf(path: Path) -> list[Document]:
    """One Document per page, with the page number in metadata (for citations)."""
    reader = PdfReader(str(path))
    return [
        Document(page_content=page.extract_text() or "", metadata={"source": path.name, "page": i + 1})
        for i, page in enumerate(reader.pages)
    ]


LOADERS = {".md": load_text, ".txt": load_text, ".html": load_html, ".htm": load_html, ".pdf": load_pdf}


def load_directory(directory: Path) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(directory.iterdir()):
        loader = LOADERS.get(path.suffix.lower())
        if loader:
            docs.extend(loader(path))
    return [d for d in docs if d.page_content.strip()]


def chunk_documents(docs: list[Document], chunk_size: int = 600, chunk_overlap: int = 100) -> list[Document]:
    """Split on the most meaningful boundary that fits: headings, paragraphs, lines, sentences, words."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


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
