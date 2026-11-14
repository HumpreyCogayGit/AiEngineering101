"""EXER021 stretch goal 2 — cosine vs L2 distance on the same queries.

    uv run python EXER021/stretch/goal2_cosine_vs_l2.py

The same chunks go into two collections that differ only in the distance
metric. Cosine compares direction; L2 (Euclidean) also sees length.

When every vector has length 1, the two always rank identically, because
squared L2 = 2 x cosine distance. Many embedding models return unit-length
vectors, and the script prints the length so you can tell which case you are in.
"""

from __future__ import annotations

import tempfile

import chromadb
import numpy as np
from langchain_chroma import Chroma

from aicourse.llm import get_embeddings
from aicourse.rag import load_knowledge_base, split_documents
from aicourse.stretch import solution_module

base = solution_module(__file__, "vector_store.py")

QUERIES = ["Can I bring my dog?", "How much is express delivery?", "vacation days for staff"]


def open_store(folder: str, embeddings, space: str) -> Chroma:
    client = chromadb.PersistentClient(path=folder, settings=chromadb.Settings(anonymized_telemetry=False))
    return Chroma(client=client, collection_name=f"stretch_{space}", embedding_function=embeddings,
                  collection_metadata={"hnsw:space": space})


def main() -> None:
    embeddings = get_embeddings()
    chunks = split_documents(load_knowledge_base())
    length = float(np.linalg.norm(embeddings.embed_query("hello")))
    print(f"Length of a vector from your embedding model: {length:.4f}"
          f"  ({'unit length' if abs(length - 1) < 0.01 else 'NOT unit length'})\n")

    with tempfile.TemporaryDirectory() as folder:
        stores = {space: open_store(folder, embeddings, space) for space in ("cosine", "l2")}
        for store in stores.values():
            base.add_chunks(store, chunks)
        same = 0
        for query in QUERIES:
            print(f"Query: {query}")
            ranked = {}
            for space, store in stores.items():
                results = base.search(store, query, k=3)
                ranked[space] = [base.make_id(doc) for doc, _ in results]
                shown = "  ".join(f"{doc.metadata['source']}={distance:.3f}" for doc, distance in results)
                print(f"  {space:<6} {shown}")
            same += ranked["cosine"] == ranked["l2"]
        print(f"\nSame top-3 order for {same} of {len(QUERIES)} queries.")
        print("With unit-length vectors the order is always the same and l2 = 2 x cosine distance.")


if __name__ == "__main__":
    main()
