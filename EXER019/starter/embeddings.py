"""EXER019 — Embeddings and Similarity.

An embedding model turns text into a vector (a list of numbers). Texts with
similar MEANING get vectors that point in similar directions — even when
they share no words. Cosine similarity measures that direction.

    uv run python EXER019/starter/embeddings.py
    uv run python EXER019/check.py
"""

from __future__ import annotations

import numpy as np

from aicourse.llm import get_openai_client
from aicourse.settings import get_settings

CORPUS = [
    "You can return unopened beans within 30 days for a full refund.",
    "Standard shipping is free for orders over 1,500 pesos.",
    "Cold brew should steep in the fridge for 16 to 18 hours.",
    "Our Makati café opens at 6:30 in the morning.",
    "Earn one reward star for every 50 pesos you spend.",
    "Barako Bold is a strong, smoky dark roast from Batangas.",
    "Employees get 15 days of paid vacation per year.",
    "Keep coffee beans in an airtight container away from light.",
]


def embed_texts(client, texts: list[str]) -> list[list[float]]:
    """Embed many texts in ONE API call.

    response = client.embeddings.create(model=<embedding deployment>, input=texts)
    response.data is a list of items with .index and .embedding.
    Return the embeddings in the same order as `texts` (sort by .index to be safe).
    """
    # TODO
    raise NotImplementedError("embed_texts")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """cos(θ) = (a · b) / (|a| * |b|).  1 = same direction, 0 = unrelated.

    Use numpy: np.asarray(...), the @ operator for the dot product, np.linalg.norm for |a|.
    Return 0.0 if either vector has zero length. Return a plain Python float.
    """
    # TODO
    raise NotImplementedError("cosine_similarity")


def search(
    query_vector: list[float], corpus: list[str], corpus_vectors: list[list[float]], k: int = 3
) -> list[tuple[str, float]]:
    """Score every corpus text against the query and return the top k
    (text, score) pairs, best first."""
    # TODO
    raise NotImplementedError("search")


def main() -> None:
    client = get_openai_client()
    vectors = embed_texts(client, CORPUS)
    print(f"Embedded {len(vectors)} sentences; each vector has {len(vectors[0])} dimensions.")
    print("First 5 numbers of the first vector:", [round(x, 4) for x in vectors[0][:5]])

    for query in ["How do I get my money back?", "When can I take a holiday from work?",
                  "What time does the shop open?", "How should I store coffee?"]:
        q_vec = embed_texts(client, [query])[0]
        print(f"\nQuery: {query}")
        for text, score in search(q_vec, CORPUS, vectors, k=2):
            print(f"  {score:.3f}  {text}")


if __name__ == "__main__":
    main()
