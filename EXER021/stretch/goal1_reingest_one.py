"""EXER021 stretch goal 1 — re-ingest one changed document, leave the others alone.

    uv run python EXER021/stretch/goal1_reingest_one.py     # offline: fake embeddings, temp folder

A document was edited. Its chunks get new content-based ids, so plain
add_chunks() would ADD the new text and KEEP the stale chunks. Re-ingesting a
source therefore has two halves:

1. delete the chunks of that source which no longer exist (found by metadata),
2. add the chunks that are new.

Chunks whose text did not change keep their id: they are neither deleted nor
embedded again. Nothing from any other source is touched.
"""

from __future__ import annotations

import tempfile

from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding

from aicourse.rag import load_knowledge_base, split_documents
from aicourse.stretch import solution_module

base = solution_module(__file__, "vector_store.py")


def reingest_source(store, source: str, new_chunks: list[Document]) -> dict[str, int]:
    """Make the store hold exactly `new_chunks` for `source`. Returns what changed."""
    if any(c.metadata.get("source") != source for c in new_chunks):
        raise ValueError(f"every chunk must belong to {source}")
    old_ids = set(store.get(where={"source": source})["ids"])
    new_ids = {base.make_id(c) for c in new_chunks}
    stale = sorted(old_ids - new_ids)
    if stale:
        store.delete(ids=stale)
    added = base.add_chunks(store, new_chunks)  # idempotent: skips ids that are still there
    return {"deleted": len(stale), "added": added, "unchanged": len(old_ids & new_ids)}


def main() -> None:
    docs = load_knowledge_base()
    with tempfile.TemporaryDirectory() as folder:
        store = base.open_store(folder, DeterministicFakeEmbedding(size=64), collection="stretch_reingest")
        base.add_chunks(store, split_documents(docs))
        others_before = {i for i, m in zip(*[store.get()[k] for k in ("ids", "metadatas")])
                         if m["source"] != "shipping.md"}
        print(f"Indexed {base.count(store)} chunks.")

        # The shipping fee changes: one sentence in one document.
        edited = [Document(page_content=d.page_content.replace("Express shipping costs ₱250",
                                                               "Express shipping costs ₱300"),
                           metadata=d.metadata) for d in docs if d.metadata["source"] == "shipping.md"]
        result = reingest_source(store, "shipping.md", split_documents(edited))
        print(f"Re-ingested shipping.md: {result}")

        others_after = {i for i, m in zip(*[store.get()[k] for k in ("ids", "metadatas")])
                        if m["source"] != "shipping.md"}
        texts = " ".join(store.get(where={"source": "shipping.md"})["documents"])
        print(f"Collection has {base.count(store)} chunks; other sources untouched: {others_before == others_after}")
        print(f"New price stored: {'₱300' in texts}; stale price gone: {'₱250' not in texts}")
        print("Second run changes nothing:", reingest_source(store, "shipping.md", split_documents(edited)))


if __name__ == "__main__":
    main()
