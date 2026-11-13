"""EXER019 checks. Run:  uv run python EXER019/check.py"""

import math

from aicourse.check import Checker
from aicourse.llm import get_llm_client

checker = Checker(__file__)
mod = checker.load("embeddings.py")


@checker.check("cosine_similarity() of identical vectors is 1")
def _():
    assert math.isclose(mod.cosine_similarity([1, 2, 3], [1, 2, 3]), 1.0)
    assert math.isclose(mod.cosine_similarity([1, 2, 3], [2, 4, 6]), 1.0), "length must not matter"


@checker.check("cosine_similarity() of orthogonal vectors is 0, opposite is -1")
def _():
    assert math.isclose(mod.cosine_similarity([1, 0], [0, 1]), 0.0, abs_tol=1e-12)
    assert math.isclose(mod.cosine_similarity([1, 0], [-1, 0]), -1.0)
    assert mod.cosine_similarity([0, 0], [1, 1]) == 0.0
    assert isinstance(mod.cosine_similarity([1, 0], [1, 0]), float)


@checker.check("search() ranks by similarity, best first, top k")
def _():
    out = mod.search([1, 0], ["a", "b", "c"], [[0, 1], [1, 0.1], [1, 1]], k=2)
    assert [t for t, _ in out] == ["b", "c"], out
    assert out[0][1] >= out[1][1]


@checker.check("embed_texts() returns one vector per text  [live API]")
def _():
    vecs = mod.embed_texts(get_llm_client(), ["hello", "world", "coffee"])
    assert len(vecs) == 3 and len(vecs[0]) > 50, (len(vecs), len(vecs[0]))


@checker.check("semantic search finds the refund sentence with no shared words  [live API]")
def _():
    client = get_llm_client()
    vectors = mod.embed_texts(client, mod.CORPUS)
    q = mod.embed_texts(client, ["How do I get my money back?"])[0]
    best_text, _ = mod.search(q, mod.CORPUS, vectors, k=1)[0]
    assert "refund" in best_text, best_text


checker.run()
