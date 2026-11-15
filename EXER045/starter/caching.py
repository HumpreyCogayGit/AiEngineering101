"""EXER045 — Caching and Batch Work (starter).

    uv run python EXER045/starter/caching.py            # the cache in front of the helpdesk (live)
    uv run python EXER045/starter/prefix_experiment.py  # does the provider cache your prompt prefix? (live)

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
    """Lowercase, collapse runs of whitespace to one space, strip, and remove trailing "?!. ".
    "  Is shipping   FREE?? " -> "is shipping free". Do not touch the words: a different word is a different question.
    """
    # TODO
    raise NotImplementedError("normalize")


def fingerprint(items: list[str]) -> str:
    """A short, order-independent hash of a list of strings (tool names and descriptions, for example)."""
    return hashlib.sha256("\n".join(sorted(items)).encode("utf-8")).hexdigest()[:16]


def cache_key(question: str, *, model: str, prompt_version: str, tools: str, policy_version: str,
              tenant: str, role: str) -> str:
    """A sha256 hex digest of everything the answer depends on.

    Build a dict {"q": normalize(question), "model": ..., "prompt": prompt_version, "tools": tools,
    "policy": policy_version, "tenant": tenant, "role": role}, serialise it with
    json.dumps(..., sort_keys=True) (same dict -> same text), and hash it.

    Why each part: a new model, prompt, tool set or guardrail policy can change the right answer.
    The tenant keeps companies apart; the role keeps staff answers (EXER042) away from customers.
    """
    # TODO
    raise NotImplementedError("cache_key")


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
        """The stored reply, or None.

        Under self.lock:
        - entry = self.entries.get(key)
        - an entry older than self.ttl (self.clock() - entry.stored_at > self.ttl): delete it,
          self.stats["expired"] += 1, and treat it as missing
        - count self.stats["hits"] or self.stats["misses"]
        - return entry.reply or None
        """
        # TODO
        raise NotImplementedError("get")

    def put(self, key: str, reply: dict) -> None:
        with self.lock:
            self.entries[key] = Entry(reply, self.clock())

    def hit_rate(self) -> float:
        total = self.stats["hits"] + self.stats["misses"]
        return self.stats["hits"] / total if total else 0.0


def cacheable(reply: dict, earlier_turns: int) -> bool:
    """May this reply be served to the next person who asks the same question?

    False when: reply["blocked"]; earlier_turns > 0 (a follow-up depends on the conversation);
    reply["tools_used"] contains a tool in SIDE_EFFECT_TOOLS; the answer is empty. Otherwise True.
    """
    # TODO
    raise NotImplementedError("cacheable")


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
    """Two messages, static first and volatile last:

      system: f"{system}\n\nDocuments:\n{documents}"                 the same for everyone, every day
      user:   f"(Customer: {customer_name}. Today: {today}.)\n\n{question}"

    Providers reuse the processing of an identical PREFIX. A date or a name near the start makes
    every prompt different from that point on.
    """
    # TODO
    raise NotImplementedError("build_messages")


# ------------------------------------------------------------------ 4. batch requests
def batch_lines(questions: list[str], model: str, system: str, url: str = "/v1/chat/completions") -> list[str]:
    """One JSON line per question (json.dumps, ensure_ascii=False), in the batch file format:

      {"custom_id": f"q-{i:04d}", "method": "POST", "url": url,
       "body": {"model": model, "messages": [{"role": "system", "content": system},
                                              {"role": "user", "content": question}]}}

    Results can come back in any order: custom_id is how you match them to the questions.
    """
    # TODO
    raise NotImplementedError("batch_lines")


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
