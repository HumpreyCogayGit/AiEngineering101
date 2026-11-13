"""EXER021 — Vector Store with Chroma (reference solution).

A vector store keeps (id, vector, text, metadata) records on disk and answers
"which records are nearest to this vector?" quickly. Chroma runs locally,
in-process, with no server to install.
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
    """Deterministic id: the same chunk always gets the same id."""
    key = f"{doc.metadata.get('source')}::{doc.page_content}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


def open_store(persist_dir: str | Path, embeddings: Embeddings, collection: str = COLLECTION) -> Chroma:
    client = chromadb.PersistentClient(
        path=str(persist_dir), settings=chromadb.Settings(anonymized_telemetry=False)
    )
    return Chroma(
        client=client,
        collection_name=collection,
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )


def add_chunks(store: Chroma, chunks: list[Document]) -> int:
    """Add chunks idempotently. Returns how many NEW chunks were added."""
    ids = [make_id(c) for c in chunks]
    existing = set(store.get(ids=ids)["ids"])
    new = [(i, c) for i, c in zip(ids, chunks) if i not in existing]
    if new:
        store.add_documents([c for _, c in new], ids=[i for i, _ in new])
    return len(new)


def count(store: Chroma) -> int:
    return store._collection.count()


def search(store: Chroma, query: str, k: int = 3, source: str | None = None) -> list[tuple[Document, float]]:
    """Similarity search with scores; optionally only within one source file."""
    where = {"source": source} if source else None
    return store.similarity_search_with_score(query, k=k, filter=where)


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
