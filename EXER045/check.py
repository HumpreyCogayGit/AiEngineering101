"""EXER045 checks. Run:  uv run python EXER045/check.py

Offline checks use a fake clock and a fake helpdesk. The live check asks your embedding model
why a semantic cache is dangerous.
"""

import json
from dataclasses import dataclass

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("caching.py")

VERSIONS = dict(model="m1", prompt_version="p1", tools="t1", policy_version="g1", tenant="nimbus", role="customer")


@dataclass(frozen=True)
class Who:
    user_id: str
    role: str = "customer"
    tenant: str = "nimbus"


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


@checker.check("normalize(): case, spaces and trailing punctuation do not matter; words do")
def _():
    assert mod.normalize("  Is shipping   FREE?? ") == mod.normalize("is shipping free") == "is shipping free"
    assert mod.normalize("Is shipping free?") != mod.normalize("Is express shipping free?")


@checker.check("cache_key(): the same for the same question, different when anything the answer depends on changes")
def _():
    base = mod.cache_key("Is shipping free?", **VERSIONS)
    assert base == mod.cache_key("is shipping free", **VERSIONS) and len(base) >= 32
    for field, other in [("model", "m2"), ("prompt_version", "p2"), ("tools", "t2"), ("policy_version", "g2"),
                         ("tenant", "other-company"), ("role", "staff")]:
        assert mod.cache_key("Is shipping free?", **{**VERSIONS, field: other}) != base, f"{field} must be in the key"
    assert "shipping" not in base, "hash the key: it may end up in logs and metrics"


@checker.check("ResponseCache.get(): hit, miss, and an expired entry is removed and counted")
def _():
    clock = Clock()
    cache = mod.ResponseCache(ttl_seconds=60, clock=clock)
    assert cache.get("k") is None
    cache.put("k", {"answer": "yes"})
    clock.now = 59
    assert cache.get("k") == {"answer": "yes"}
    clock.now = 61
    assert cache.get("k") is None and "k" not in cache.entries
    assert cache.stats == {"hits": 1, "misses": 2, "expired": 1}, cache.stats
    assert abs(cache.hit_rate() - 1 / 3) < 1e-9


@checker.check("cacheable(): never blocked replies, follow-up turns, or answers that changed something")
def _():
    good = {"answer": "Free over ₱1,500.", "tools_used": ["search_knowledge_base"], "blocked": False}
    assert mod.cacheable(good, earlier_turns=0)
    assert not mod.cacheable({**good, "blocked": True}, 0)
    assert not mod.cacheable(good, earlier_turns=1), "a follow-up depends on the conversation"
    assert not mod.cacheable({**good, "tools_used": ["notes_add_note"]}, 0), "replaying 'saved' saves nothing"
    assert not mod.cacheable({**good, "answer": ""}, 0)


@checker.check("CachedHelpdesk: a repeat is served without the model, but never across tenants or roles")
def _():
    calls = []

    def ask(question, key, principal):
        calls.append((question, principal.user_id))
        return {"answer": f"answer for {principal.role}", "tools_used": [], "blocked": False, "reasons": [],
                "tokens": 1000}

    helpdesk = mod.CachedHelpdesk(ask, mod.ResponseCache(3600), model="m", prompt_version="p", tools="t",
                                  policy_version="g")
    first = helpdesk.ask("Is shipping free?", "ana/1", Who("ana"))
    again = helpdesk.ask("is shipping free", "ben/1", Who("ben"))
    assert not first["cached"] and again["cached"] and again["tokens"] == 0 and len(calls) == 1, (first, again)
    helpdesk.ask("Is shipping free?", "zed/1", Who("zed", tenant="other-company"))
    helpdesk.ask("Is shipping free?", "maya/1", Who("maya", role="staff"))
    assert len(calls) == 3, "another tenant and another role must reach the model"
    helpdesk.ask("Is shipping free?", "ana/1", Who("ana"))  # second turn of ana's thread
    assert len(calls) == 4, "a follow-up turn is never answered from the cache"


@checker.check("build_messages(): two customers on two days share the whole prompt up to the volatile part")
def _():
    a = json.dumps(mod.build_messages("SYS", "DOCS" * 50, "Ana", "2026-11-15", "Is shipping free?"))
    b = json.dumps(mod.build_messages("SYS", "DOCS" * 50, "Ben", "2026-12-01", "Is shipping free?"))
    shared = next(i for i, (x, y) in enumerate(zip(a, b)) if x != y)
    assert shared > len("DOCS" * 50), "the static system prompt and documents must come first"
    for text in (a, b):
        assert text.index("DOCS") < text.index("Ana" if "Ana" in text else "Ben") < text.index("Is shipping free?")


@checker.check("batch_lines(): one JSON request per line, each with a unique custom_id")
def _():
    lines = mod.batch_lines(["Is shipping free?", "Do you ship to Japan?"], model="m", system="S")
    rows = [json.loads(line) for line in lines]
    assert len(rows) == 2 and all("\n" not in line for line in lines)
    assert len({r["custom_id"] for r in rows}) == 2
    assert all(r["method"] == "POST" and r["url"].endswith("/chat/completions") for r in rows)
    assert rows[1]["body"]["model"] == "m" and rows[1]["body"]["messages"][-1]["content"] == "Do you ship to Japan?"


@checker.check("semantic caching is unsafe: no similarity threshold separates paraphrases from different questions  [live API]")
def _():
    import numpy as np

    from aicourse.llm import get_embeddings

    embeddings = get_embeddings()

    def similarity(a, b):
        va, vb = np.array(embeddings.embed_query(a)), np.array(embeddings.embed_query(b))
        return float(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)))

    different_answers = [("Can I return unopened beans?", "Can I return opened beans?"),            # 30 vs 14 days
                         ("How much is express shipping to Cebu?", "How much is standard shipping to Cebu?"),
                         ("Is the Maginhawa café open on Mondays?", "Is the Makati café open on Mondays?")]
    same_answers = [("Is shipping free?", "Do you ship for free?"),
                    ("How long does a refund take?", "When will I get my money back?"),
                    ("Do you deliver to Japan?", "Can I get my order shipped to Japan?")]
    wrong = [similarity(*pair) for pair in different_answers]
    right = [similarity(*pair) for pair in same_answers]
    print(f"         different answers: {', '.join(f'{s:.3f}' for s in wrong)}   "
          f"paraphrases: {', '.join(f'{s:.3f}' for s in right)}")
    # The hazard: any threshold low enough to accept every paraphrase also accepts a question with another answer.
    assert max(wrong) > min(right), "these pairs happen to separate on this model; try more pairs of your own"


checker.run()
