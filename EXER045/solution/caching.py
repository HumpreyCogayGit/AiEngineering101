"""EXER045 — Caching and Batch Work (reference solution).

    uv run python EXER045/solution/caching.py            # the cache in front of the helpdesk (live)
    uv run python EXER045/solution/prefix_experiment.py  # does the provider cache your prompt prefix? (live)

Three ways to pay less for the same answers, each with its own hazard:

1. A RESPONSE CACHE returns a stored answer for a repeated question without
   calling the model. Hazard: returning an answer that is no longer right, or
   that was right for someone else. So the key holds everything the answer
   depends on (model, prompt version, tools, policy, TENANT), entries expire,
   and personal or side-effecting answers are never stored.
2. PROMPT-PREFIX CACHING happens at the provider: when the start of a prompt
   repeats exactly, its processing is reused, cheaper and faster. Your only job
   is to keep the start of the prompt identical: static parts first.
3. BATCH ENDPOINTS take a file of requests and answer within hours, for about
   half the price where a provider offers them. Right for evaluations and bulk
   jobs, wrong for anything a user is waiting for.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from dataclasses import dataclass
from typing import Callable

SIDE_EFFECT_TOOLS = {"notes_add_note"}  # an answer that changed something must run again, every time


# ------------------------------------------------------------------ 1. the key
def normalize(question: str) -> str:
    """Lowercase, single spaces, no trailing punctuation: "Is shipping free?" == "is shipping  free"."""
    return re.sub(r"\s+", " ", question).strip().lower().rstrip("?!. ")


def fingerprint(items: list[str]) -> str:
    """A short, order-independent hash of a list of strings (tool names and descriptions, for example)."""
    return hashlib.sha256("\n".join(sorted(items)).encode("utf-8")).hexdigest()[:16]


def cache_key(question: str, *, model: str, prompt_version: str, tools: str, policy_version: str,
              tenant: str, role: str) -> str:
    """Everything the answer depends on goes into the key. Leave one out, and a change to it
    serves stale answers. Leave out the tenant, and one company's answer reaches another; leave
    out the role, and a staff answer (from staff-only documents, EXER042) reaches a customer."""
    parts = {"q": normalize(question), "model": model, "prompt": prompt_version, "tools": tools,
             "policy": policy_version, "tenant": tenant, "role": role}
    return hashlib.sha256(json.dumps(parts, sort_keys=True).encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ 2. the cache
@dataclass
class Entry:
    reply: dict
    stored_at: float


class ResponseCache:
    """An in-memory exact-match cache with a time to live. (Production: Redis or similar, shared by replicas.)"""

    def __init__(self, ttl_seconds: float, clock: Callable[[], float] = time.monotonic) -> None:
        self.ttl = ttl_seconds
        self.clock = clock
        self.entries: dict[str, Entry] = {}
        self.stats = {"hits": 0, "misses": 0, "expired": 0}
        self.lock = threading.Lock()

    def get(self, key: str) -> dict | None:
        """The stored reply, or None. An expired entry is removed and counted as 'expired' (and a miss)."""
        with self.lock:
            entry = self.entries.get(key)
            if entry is not None and self.clock() - entry.stored_at > self.ttl:
                del self.entries[key]
                self.stats["expired"] += 1
                entry = None
            self.stats["hits" if entry else "misses"] += 1
            return entry.reply if entry else None

    def put(self, key: str, reply: dict) -> None:
        with self.lock:
            self.entries[key] = Entry(reply, self.clock())

    def hit_rate(self) -> float:
        total = self.stats["hits"] + self.stats["misses"]
        return self.stats["hits"] / total if total else 0.0


def cacheable(reply: dict, earlier_turns: int) -> bool:
    """May this reply be served to the next person who asks the same question?"""
    if reply.get("blocked"):
        return False  # guardrails are cheap; run them every time
    if earlier_turns > 0:
        return False  # the answer may depend on the conversation ("and to Cebu?")
    if SIDE_EFFECT_TOOLS & set(reply.get("tools_used", [])):
        return False  # "saved your note" must not be replayed without saving it
    return bool(reply.get("answer"))


class CachedHelpdesk:
    """Wraps an `ask(question, key, principal)` helpdesk (EXER042) with the response cache (given)."""

    def __init__(self, ask: Callable, cache: ResponseCache, *, model: str, prompt_version: str, tools: str,
                 policy_version: str) -> None:
        self.ask_uncached = ask
        self.cache = cache
        self.versions = {"model": model, "prompt_version": prompt_version, "tools": tools,
                         "policy_version": policy_version}
        self.turns: dict[str, int] = {}
        self.lock = threading.Lock()

    def ask(self, question: str, key: str, principal) -> dict:
        with self.lock:
            earlier = self.turns.get(key, 0)
            self.turns[key] = earlier + 1
        ckey = cache_key(question, tenant=getattr(principal, "tenant", "default"), role=principal.role,
                         **self.versions)
        if earlier == 0:
            cached = self.cache.get(ckey)
            if cached is not None:
                return {**cached, "cached": True, "tokens": 0}
        reply = self.ask_uncached(question, key, principal)
        if cacheable(reply, earlier):
            self.cache.put(ckey, reply)
        return {**reply, "cached": False}


# ------------------------------------------------------------------ 3. prompts that share a prefix
def build_messages(system: str, documents: str, customer_name: str, today: str, question: str) -> list[dict]:
    """Static first, volatile last. The provider can reuse the processing of an identical PREFIX only:
    one changed character early in the prompt (a date, a name) makes everything after it new."""
    return [
        {"role": "system", "content": f"{system}\n\nDocuments:\n{documents}"},
        {"role": "user", "content": f"(Customer: {customer_name}. Today: {today}.)\n\n{question}"},
    ]


# ------------------------------------------------------------------ 4. batch requests
def batch_lines(questions: list[str], model: str, system: str, url: str = "/v1/chat/completions") -> list[str]:
    """One JSON line per request, in the batch file format of OpenAI-compatible batch APIs.
    custom_id is how you match answers to questions: results may come back in any order."""
    return [json.dumps({"custom_id": f"q-{i:04d}", "method": "POST", "url": url,
                        "body": {"model": model, "messages": [{"role": "system", "content": system},
                                                              {"role": "user", "content": q}]}},
                       ensure_ascii=False)
            for i, q in enumerate(questions)]


# ------------------------------------------------------------------ demo (given)
def main() -> None:
    import sys
    from dataclasses import dataclass as _dc

    from aicourse.settings import get_settings
    from aicourse.stretch import solution_of

    secure = solution_of("EXER042", "secure_service.py")
    sys.path.insert(0, str(secure.base.capstone_dir()))
    import assistant as capstone

    @_dc(frozen=True)
    class Customer:
        user_id: str
        role: str = "customer"
        tenant: str = "nimbus"

    helpdesk = secure.UserHelpdesks()
    cache = ResponseCache(ttl_seconds=3600)
    cached = CachedHelpdesk(lambda q, k, p: helpdesk.ask(q, k, secure.Principal(p.user_id, p.role)), cache,
                            model=get_settings().chat_model,
                            prompt_version=fingerprint([capstone.SYSTEM_PROMPT]),
                            tools=fingerprint(["search_knowledge_base", "calculator", "notes_add_note",
                                               "notes_list_notes", "notes_search_notes"]),
                            policy_version="guards-v1")
    questions = [("ana", "Is shipping free?"), ("ben", "is shipping free"), ("ana", "Do you ship for free?"),
                 ("carla", "Is shipping free?"), ("ana", "Save a note titled 'x' saying y.")]
    for i, (user, question) in enumerate(questions):
        start = time.perf_counter()
        reply = cached.ask(question, f"{user}/t{i}", Customer(user))
        print(f"{'HIT ' if reply['cached'] else 'MISS'} {time.perf_counter() - start:5.2f}s {reply['tokens']:>5} tokens  "
              f"{user:<6}{question}")
    print(f"\nhit rate {cache.hit_rate():.0%}  {cache.stats}")
    print("'Do you ship for free?' missed: an exact cache only matches the same words. That is the safe side.")


if __name__ == "__main__":
    main()
