"""EXER019 stretch goal 1 — embed in batches, cache vectors on disk by text hash.

    uv run python EXER019/stretch/goal1_cached_embeddings.py     # run it twice

Embedding the same text twice gives the same vector, so pay for it once.
The cache key is a hash of the MODEL NAME plus the text: vectors from
different models are not comparable, so they must never share a key.
Uncached texts are sent in batches, because one request per text is slow and
one request for 100,000 texts is too large.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from aicourse.llm import get_llm_client
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "embeddings.py")

CACHE_FILE = Path(__file__).resolve().parent / "output" / "embedding_cache.json"


class CachedEmbedder:
    def __init__(self, client, cache_file: Path = CACHE_FILE, batch_size: int = 5) -> None:
        self.client = client
        self.cache_file = cache_file
        self.batch_size = batch_size
        self.api_calls = 0
        try:
            self.cache: dict[str, list[float]] = json.loads(cache_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.cache = {}

    @staticmethod
    def key(text: str) -> str:
        return hashlib.sha256(f"{get_settings().embedding_model}::{text}".encode()).hexdigest()

    def embed(self, texts: list[str]) -> list[list[float]]:
        missing = list(dict.fromkeys(t for t in texts if self.key(t) not in self.cache))  # unique, in order
        for start in range(0, len(missing), self.batch_size):
            batch = missing[start : start + self.batch_size]
            for text, vector in zip(batch, base.embed_texts(self.client, batch)):
                self.cache[self.key(text)] = vector
            self.api_calls += 1
        if missing:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.cache_file.write_text(json.dumps(self.cache), encoding="utf-8")
        return [self.cache[self.key(t)] for t in texts]


def main() -> None:
    embedder = CachedEmbedder(get_llm_client())
    before = len(embedder.cache)
    vectors = embedder.embed(base.CORPUS)
    print(f"{len(base.CORPUS)} sentences: {len(embedder.cache) - before} newly embedded in "
          f"{embedder.api_calls} request(s) of up to {embedder.batch_size}; {before} were already cached.")

    query = "How do I get my money back?"
    q_vec = embedder.embed([query])[0]
    print(f"\nQuery: {query}")
    for text, score in base.search(q_vec, base.CORPUS, vectors, k=2):
        print(f"  {score:.3f}  {text}")
    print(f"\nRun it again: 0 requests. Cache: {CACHE_FILE.relative_to(CACHE_FILE.parents[3])}")


if __name__ == "__main__":
    main()
