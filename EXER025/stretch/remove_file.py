"""EXER025 stretch goal 1 (logic) — remove one file from a session index.

    uv run python EXER025/stretch/remove_file.py      # offline: fake embeddings

Every chunk carries its file name in `metadata["source"]`, which is what
makes this possible: ask the store for the ids with that source and delete
them. The other files' chunks, and their embeddings, are untouched.
The app that uses this is goal1_remove_file_app.py.
"""

from __future__ import annotations

from aicourse.stretch import solution_module

logic = solution_module(__file__, "docs_logic.py")


def indexed_files(store) -> list[str]:
    return sorted({m["source"] for m in store.get()["metadatas"]})


def remove_file(store, source: str) -> int:
    """Delete every chunk of one file. Returns how many chunks were removed."""
    ids = store.get(where={"source": source})["ids"]
    if ids:
        store.delete(ids=ids)
    return len(ids)


def main() -> None:
    from langchain_core.embeddings import DeterministicFakeEmbedding

    from aicourse.rag import KB_DIR

    docs = []
    for name in ("shipping.md", "refund_policy.md", "products.md"):
        docs += logic.load_uploaded(name, (KB_DIR / name).read_bytes())
    store = logic.build_index(docs, DeterministicFakeEmbedding(size=64))
    print("Indexed:", indexed_files(store), f"({store._collection.count()} chunks)")
    print("Removed", remove_file(store, "refund_policy.md"), "chunks of refund_policy.md")
    print("Indexed:", indexed_files(store), f"({store._collection.count()} chunks)")
    hits = {d.metadata["source"] for d in store.similarity_search("refund", k=10)}
    print("refund_policy.md can still be retrieved:", "refund_policy.md" in hits)


if __name__ == "__main__":
    main()
