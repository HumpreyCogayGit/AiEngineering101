"""EXER040 stretch goal 1 — do not report "ready" before the vector index exists.

    uv run python EXER040/stretch/goal1_index_readiness.py      # offline: a temporary, empty index folder

The first question to a fresh container is slow: the knowledge base is
embedded and indexed on first use. With the exercise's checks the container
says "ready" long before that, and the first customer pays for it.

Two additions fix it:
- a readiness check that looks at the index WITHOUT building it,
- a warm-up thread, started with the service, that builds it.

Until the warm-up is done, /readyz answers 503 and the platform sends no
traffic. /healthz stays 200 the whole time: slow to start is not broken.
"""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path

import chromadb

from aicourse.stretch import solution_module

base = solution_module(__file__, "service.py")


def index_size(chroma_path: Path, collection: str) -> int:
    """Chunks in the collection; 0 when the folder or the collection does not exist. No embedding call."""
    if not chroma_path.is_dir():
        return 0
    client = chromadb.PersistentClient(path=str(chroma_path), settings=chromadb.Settings(anonymized_telemetry=False))
    try:
        return client.get_collection(collection).count()
    except Exception:  # the collection has not been created yet
        return 0


def make_index_check(chroma_path: Path, collection: str):
    def check_index() -> None:
        if index_size(chroma_path, collection) == 0:
            raise RuntimeError("the vector index is not built yet")
    return check_index


def warm_up_in_background(build) -> threading.Thread:
    """Build the index without blocking start-up. `build` is aicourse.rag.get_vector_store in the real service."""
    thread = threading.Thread(target=build, daemon=True, name="warm-up")
    thread.start()
    return thread


def checks_for_service() -> dict:
    """The exercise's readiness checks plus the index check, for the configured store."""
    from aicourse.rag import default_collection_name
    from aicourse.settings import get_settings

    return {**base.READINESS_CHECKS, "index": make_index_check(get_settings().chroma_path, default_collection_name())}


def main() -> None:
    with tempfile.TemporaryDirectory() as folder:
        path, name = Path(folder), "demo_kb"
        checks = {"knowledge_base": base.check_knowledge_base, "index": make_index_check(path, name)}

        def build() -> None:  # stands in for get_vector_store(): creates the collection and adds chunks
            client = chromadb.PersistentClient(path=str(path), settings=chromadb.Settings(anonymized_telemetry=False))
            client.get_or_create_collection(name).add(ids=["1", "2"], embeddings=[[0.1, 0.2], [0.3, 0.4]],
                                                      documents=["chunk one", "chunk two"])

        print("at start      :", base.readiness(checks), "  liveness:", base.liveness())
        warm_up_in_background(build).join()
        print("after warm-up :", base.readiness(checks))
    print("\nIn service.py: start warm_up_in_background(get_vector_store) in main(), and pass checks_for_service() to readiness().")


if __name__ == "__main__":
    main()
