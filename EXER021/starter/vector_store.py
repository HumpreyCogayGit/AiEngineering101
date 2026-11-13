"""EXER021 — Vector Store with Chroma.

A vector store keeps (id, vector, text, metadata) records on disk and answers
"which records are nearest to this vector?" quickly. Chroma runs locally,
in-process, with no server to install.

The loading/chunking from EXER020 is available as aicourse.rag.load_knowledge_base()
and aicourse.rag.split_documents().

    uv run python EXER021/starter/vector_store.py
    uv run python EXER021/check.py
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from aicourse.llm import get_embeddings
from aicourse.rag import load_knowledge_base, split_documents
from aicourse.settings import get_settings

COLLECTION = "exer021_kb"


def make_id(doc: Document) -> str:
    """Deterministic id: the same chunk must always get the same id.

    Hash f"{source}::{page_content}" with hashlib.sha256 and keep the first 32 hex characters.
    """
    # TODO
    raise NotImplementedError("make_id")


def open_store(persist_dir: str | Path, embeddings: Embeddings, collection: str = COLLECTION) -> Chroma:
    """Open (or create) a persistent Chroma collection.

    client = chromadb.PersistentClient(path=str(persist_dir),
                                       settings=chromadb.Settings(anonymized_telemetry=False))
    return Chroma(client=client, collection_name=collection, embedding_function=embeddings,
                  collection_metadata={"hnsw:space": "cosine"})
    """
    # TODO
    raise NotImplementedError("open_store")


def add_chunks(store: Chroma, chunks: list[Document]) -> int:
    """Add chunks IDEMPOTENTLY (running twice must not create duplicates).

    1. ids = [make_id(c) for c in chunks]
    2. existing = set(store.get(ids=ids)["ids"])
    3. add only the chunks whose id is not in existing: store.add_documents(docs, ids=ids)
    4. return how many were added
    """
    # TODO
    raise NotImplementedError("add_chunks")


def count(store: Chroma) -> int:
    return store._collection.count()


def search(store: Chroma, query: str, k: int = 3, source: str | None = None) -> list[tuple[Document, float]]:
    """store.similarity_search_with_score(query, k=k, filter=...)

    When `source` is given, pass filter={"source": source} so only that file is searched.
    Returns (Document, distance) pairs — with cosine distance, SMALLER is more similar.
    """
    # TODO
    raise NotImplementedError("search")


def main() -> None:
    persist_dir = get_settings().chroma_path
    store = open_store(persist_dir, get_embeddings())
    chunks = split_documents(load_knowledge_base())
    added = add_chunks(store, chunks)
    print(f"Added {added} new chunks; collection now has {count(store)} chunks (stored in {persist_dir}).")
    print("Run me again: 0 new chunks should be added.\n")

    for query in ["Can I bring my dog?", "How much is express delivery?", "vacation days for staff"]:
        print(f"Query: {query}")
        for doc, distance in search(store, query, k=2):
            print(f"  distance={distance:.3f}  [{doc.metadata['source']}] {doc.page_content[:70]!r}")
    print("\nFiltered to shipping.md only:")
    for doc, distance in search(store, "How long does it take?", k=2, source="shipping.md"):
        print(f"  distance={distance:.3f}  [{doc.metadata['source']}] {doc.page_content[:70]!r}")


if __name__ == "__main__":
    main()
