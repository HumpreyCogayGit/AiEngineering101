"""EXER019 — Embeddings and Similarity (reference solution).

An embedding model turns text into a vector (a list of numbers). Texts with
similar MEANING get vectors that point in similar directions — even when
they share no words. Cosine similarity measures that direction.
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
    """One API call can embed many texts at once."""
    response = client.embeddings.create(model=get_settings().embedding_deployment, input=texts)
    return [item.embedding for item in sorted(response.data, key=lambda d: d.index)]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """cos(θ) = (a · b) / (|a| * |b|).  1 = same direction, 0 = unrelated."""
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    return float(va @ vb / denom) if denom else 0.0


def search(
    query_vector: list[float], corpus: list[str], corpus_vectors: list[list[float]], k: int = 3
) -> list[tuple[str, float]]:
    """Return the k most similar (text, score) pairs, best first."""
    scored = [(text, cosine_similarity(query_vector, vec)) for text, vec in zip(corpus, corpus_vectors)]
    return sorted(scored, key=lambda pair: pair[1], reverse=True)[:k]


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
