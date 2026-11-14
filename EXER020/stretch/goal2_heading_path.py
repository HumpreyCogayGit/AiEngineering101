"""EXER020 stretch goal 2 — record each chunk's heading path in its metadata.

    uv run python EXER020/stretch/goal2_heading_path.py     # offline

A chunk that says "Use a 1:15 ratio with a coarse grind" is useless without
knowing it is about the French press. The heading path
("Brewing Guide > French press") travels with the chunk as metadata, and
EXER022 can print it next to the source so the model and the reader see it.

This works with the exercise's own splitter: `add_start_index=True` records
where each chunk starts, and the headings above that position are its path.
"""

from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from aicourse.stretch import solution_module

base = solution_module(__file__, "ingest.py")

HEADING = re.compile(r"^(#{1,3}) +(.+?)\s*$", re.MULTILINE)


def heading_path(text: str, position: int) -> str:
    """The headings in force at `position`, e.g. "Brewing Guide > French press"."""
    levels: dict[int, str] = {}
    for match in HEADING.finditer(text):
        if match.start() > position:
            break
        level = len(match.group(1))
        levels[level] = match.group(2)
        for deeper in [l for l in levels if l > level]:  # a new "##" ends the previous "###"
            del levels[deeper]
    return " > ".join(levels[level] for level in sorted(levels))


def chunk_with_headings(docs: list[Document], chunk_size: int = 600, chunk_overlap: int = 100) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, add_start_index=True,
        separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Document] = []
    for doc in docs:
        for chunk in splitter.split_documents([doc]):
            start = chunk.metadata.pop("start_index")
            if doc.metadata["source"].endswith(".md"):
                # +3: a chunk that itself begins with "## Title" belongs to that heading.
                chunk.metadata["heading_path"] = heading_path(doc.page_content, start + 3)
            chunks.append(chunk)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


def format_docs(docs: list[Document]) -> str:
    """EXER022's format_docs, with the heading path next to the source."""
    def label(d: Document) -> str:
        path = d.metadata.get("heading_path")
        return f"{d.metadata['source']} > {path}" if path else d.metadata["source"]

    return "\n\n".join(f"[{i}] (source: {label(d)})\n{d.page_content}" for i, d in enumerate(docs, 1))


def main() -> None:
    chunks = chunk_with_headings(base.load_directory(base.KB_DIR), chunk_size=300, chunk_overlap=40)
    print(f"{len(chunks)} chunks. Heading paths:")
    for chunk in chunks:
        if chunk.metadata["source"] in ("brewing_guide.md", "shipping.md"):
            print(f"  {chunk.metadata['source']:<17} {chunk.metadata['heading_path']:<42} "
                  f"{chunk.page_content[:38]!r}")
    orphan = next(c for c in chunks if c.metadata.get("heading_path", "").endswith("French press"))
    print("\nIn a prompt (EXER022):\n" + format_docs([orphan]))


if __name__ == "__main__":
    main()
