"""EXER020 stretch goal 1 — a Markdown-header-aware splitter, compared.

    uv run python EXER020/stretch/goal1_markdown_splitter.py     # offline

The recursive splitter treats "\\n## " as a good place to cut, but it still
packs neighbouring sections into one chunk when they fit. A header-aware
splitter cuts at EVERY heading, so each chunk is exactly one section, and it
records the headings above the chunk in its metadata.

Only Markdown has headings: the other formats keep the recursive splitter.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from aicourse.stretch import solution_module

base = solution_module(__file__, "ingest.py")

HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]


def chunk_by_headers(docs: list[Document], chunk_size: int = 600, chunk_overlap: int = 100) -> list[Document]:
    by_header = MarkdownHeaderTextSplitter(HEADERS, strip_headers=False)  # keep the heading text in the chunk
    by_size = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks: list[Document] = []
    for doc in docs:
        if not doc.metadata["source"].endswith(".md"):
            chunks.extend(base.chunk_documents([doc], chunk_size, chunk_overlap))
            continue
        for section in by_header.split_text(doc.page_content):
            section.metadata = {**doc.metadata, **section.metadata}  # source + h1/h2
            chunks.extend(by_size.split_documents([section]))        # a long section is still cut by size
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


def sections_per_chunk(chunks: list[Document]) -> float:
    """How many '## ' sections an average Markdown chunk holds. 1.0 = one idea per chunk."""
    md = [c for c in chunks if c.metadata["source"].endswith(".md")]
    return sum(max(1, c.page_content.count("\n## ") + c.page_content.startswith("## ")) for c in md) / len(md)


def main() -> None:
    docs = base.load_directory(base.KB_DIR)
    recursive = base.chunk_documents(docs)
    by_headers = chunk_by_headers(docs)
    for name, chunks in (("recursive", recursive), ("header-aware", by_headers)):
        print(f"{name:<13} {base.chunk_stats(chunks)}  sections per Markdown chunk: {sections_per_chunk(chunks):.2f}")

    def first(chunks, source):
        return next(c for c in chunks if c.metadata["source"] == source)

    print("\nFirst chunk of brewing_guide.md, recursive:")
    print("  " + first(recursive, "brewing_guide.md").page_content[:330].replace("\n", "\n  "))
    chunk = next(c for c in by_headers if c.metadata.get("h2") == "French press")
    print(f"\nThe French press section, header-aware. metadata={chunk.metadata}")
    print("  " + chunk.page_content.replace("\n", "\n  "))


if __name__ == "__main__":
    main()
