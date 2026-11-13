"""EXER023 — Better Retrieval (reference solution).

Plain vector search fails in predictable ways: exact terms (codes, names,
numbers), vague questions, and near-duplicate results. Fixes:
  - BM25 keyword search  + vector search, merged with Reciprocal Rank Fusion
  - MMR                  to diversify results
  - multi-query          to rephrase vague questions
  - LLM reranking        to reorder candidates by true relevance
and — most importantly — MEASURE which one helps (hit rate).
"""

from __future__ import annotations

import json
import re
from typing import Callable

from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi

from aicourse.llm import get_chat_model
from aicourse.rag import chunk_id, get_vector_store, load_knowledge_base, split_documents
from aicourse.settings import DATA_DIR

Retriever = Callable[[str], list[Document]]


# ------------------------------------------------------------------ BM25
def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Retriever:
    """Classic keyword ranking: rewards rare words that appear in both query and chunk."""

    def __init__(self, chunks: list[Document]) -> None:
        self.chunks = chunks
        self.index = BM25Okapi([tokenize(c.page_content) for c in chunks])

    def search(self, query: str, k: int = 4) -> list[Document]:
        scores = self.index.get_scores(tokenize(query))
        best = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [self.chunks[i] for i in best]


# ------------------------------------------------------------------ fusion
def reciprocal_rank_fusion(rankings: list[list[Document]], k: int = 60) -> list[Document]:
    """score(doc) = Σ 1 / (k + rank)  over every ranking the doc appears in (rank starts at 1)."""
    scores: dict[str, float] = {}
    docs: dict[str, Document] = {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            key = chunk_id(doc)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            docs[key] = doc
    return [docs[key] for key in sorted(scores, key=scores.get, reverse=True)]


# ------------------------------------------------------------------ multi-query
class Queries(BaseModel):
    queries: list[str] = Field(description="Alternative phrasings of the question")


def multi_query(llm: BaseChatModel, question: str, n: int = 3) -> list[str]:
    """The original question plus n rephrasings that use different words."""
    result = llm.with_structured_output(Queries).invoke(
        f"Write {n} different search queries that would find documents answering this "
        f"customer question. Use synonyms and more specific terms.\nQuestion: {question}"
    )
    return [question] + list(result.queries)[:n]


# ------------------------------------------------------------------ reranking
class Relevance(BaseModel):
    scores: list[int] = Field(description="One relevance score 0-10 per passage, in order")


def llm_rerank(llm: BaseChatModel, question: str, docs: list[Document], top_n: int = 4) -> list[Document]:
    passages = "\n\n".join(f"[{i}] {d.page_content[:500]}" for i, d in enumerate(docs))
    result = llm.with_structured_output(Relevance).invoke(
        f"Rate how well each passage answers the question (0 = useless, 10 = answers it fully).\n"
        f"Question: {question}\n\nPassages:\n{passages}"
    )
    scores = list(result.scores) + [0] * (len(docs) - len(result.scores))
    order = sorted(range(len(docs)), key=lambda i: scores[i], reverse=True)
    return [docs[i] for i in order[:top_n]]


# ------------------------------------------------------------------ evaluation
def hit_rate(retrieve: Retriever, dataset: list[dict], k: int = 4) -> float:
    """Fraction of questions whose expected_source is among the top-k retrieved sources."""
    rows = [r for r in dataset if r.get("expected_source")]
    hits = sum(
        r["expected_source"] in {d.metadata.get("source") for d in retrieve(r["question"])[:k]}
        for r in rows
    )
    return hits / len(rows)


def build_retrievers(k: int = 4) -> dict[str, Retriever]:
    store = get_vector_store()
    bm25 = BM25Retriever(split_documents(load_knowledge_base()))
    llm = get_chat_model(temperature=0)

    def vector(q: str) -> list[Document]:
        return store.similarity_search(q, k=k)

    def mmr(q: str) -> list[Document]:
        return store.max_marginal_relevance_search(q, k=k, fetch_k=20)

    def hybrid(q: str) -> list[Document]:
        return reciprocal_rank_fusion([store.similarity_search(q, k=10), bm25.search(q, 10)])[:k]

    def multi(q: str) -> list[Document]:
        rankings = []
        for query in multi_query(llm, q):
            rankings += [store.similarity_search(query, k=10), bm25.search(query, 10)]
        return reciprocal_rank_fusion(rankings)[:k]

    def reranked(q: str) -> list[Document]:
        return llm_rerank(llm, q, hybrid_candidates(q), top_n=k)

    def hybrid_candidates(q: str) -> list[Document]:
        return reciprocal_rank_fusion([store.similarity_search(q, k=10), bm25.search(q, 10)])[:10]

    return {"vector": vector, "mmr": mmr, "bm25": lambda q: bm25.search(q, k),
            "hybrid": hybrid, "multi-query": multi, "hybrid+rerank": reranked}


def main() -> None:
    dataset = json.loads((DATA_DIR / "eval_questions.json").read_text(encoding="utf-8"))
    questions = [r["question"] for r in dataset if r["expected_source"]]
    print(f"Hit rate on {len(questions)} questions:\n")
    print(f"  {'strategy':<14} {'@1':>5} {'@4':>5}")
    for name, retrieve in build_retrievers().items():
        # Retrieve once per question, then score the same results at two cut-offs.
        # @4: is the right document anywhere in what the model will see?
        # @1: is it ranked FIRST? This is where the strategies differ.
        results = {q: retrieve(q) for q in questions}
        print(f"  {name:<14} {hit_rate(results.__getitem__, dataset, k=1):>5.0%} "
              f"{hit_rate(results.__getitem__, dataset, k=4):>5.0%}")


if __name__ == "__main__":
    main()
