"""EXER045 stretch goal 1 — invalidate cached answers when the documents change.

    uv run python EXER045/stretch/goal1_kb_versioned_cache.py      # offline: a simulated week

A time to live bounds how long a wrong answer can live; it does not stop one.
If shipping.md changes on Wednesday and the TTL is a week, the cache keeps
serving last week's fee. The fix is to put a version of the KNOWLEDGE BASE
into the key: a hash of the documents' contents. Any edit gives a new hash,
and every old entry stops matching at once.

The simulation: 20 customers a day ask "Is shipping free?" for 7 days. On day 3
the free-shipping threshold changes from ₱1,500 to ₱2,000. It counts stale
answers served by (a) a TTL-only cache and (b) a cache whose key includes the
knowledge-base version.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from aicourse.settings import DATA_DIR
from aicourse.stretch import solution_module

base = solution_module(__file__, "caching.py")
DAY = 86_400


def kb_version(folder: Path) -> str:
    """A fingerprint of every document's name and content."""
    return base.fingerprint([f"{p.name}:{p.read_bytes().hex()}" for p in sorted(folder.iterdir()) if p.is_file()])


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


def simulate(versioned: bool) -> tuple[int, int, int]:
    with tempfile.TemporaryDirectory() as tmp:
        kb = Path(tmp)
        for doc in (DATA_DIR / "knowledge_base").iterdir():
            (kb / doc.name).write_bytes(doc.read_bytes())
        clock = Clock()
        cache = base.ResponseCache(ttl_seconds=7 * DAY, clock=clock)
        stale = model_calls = 0
        for day in range(7):
            if day == 3:  # the policy changes mid-week
                shipping = kb / "shipping.md"
                shipping.write_text(shipping.read_text(encoding="utf-8").replace("₱1,500", "₱2,000"), encoding="utf-8")
            truth = "₱2,000" if "₱2,000" in (kb / "shipping.md").read_text(encoding="utf-8") else "₱1,500"
            for customer in range(20):
                clock.now = day * DAY + customer * 600
                key = base.cache_key("Is shipping free?", model="m", prompt_version="p", tools="t",
                                     policy_version=kb_version(kb) if versioned else "g1", tenant="nimbus",
                                     role="customer")
                reply = cache.get(key)
                if reply is None:
                    model_calls += 1
                    reply = {"answer": f"Free over {truth}.", "tools_used": [], "blocked": False}
                    cache.put(key, reply)
                stale += truth not in reply["answer"]
        return stale, model_calls, 140


def main() -> None:
    for versioned in (False, True):
        stale, calls, total = simulate(versioned)
        label = "TTL + knowledge-base version" if versioned else "TTL only (7 days)          "
        print(f"{label}: {calls} model calls for {total} questions, {stale} stale answers served")
    print("\nThe version costs one extra model call after each edit and serves no stale answers. "
          "Re-index the documents and bump the version in the same deploy.")


if __name__ == "__main__":
    main()
