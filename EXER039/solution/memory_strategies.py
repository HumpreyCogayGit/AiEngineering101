"""EXER039 — Conversation Memory Strategies (reference solution).

A conversation that outgrows its budget has to lose something. There are
three standard ways to choose what, and each one forgets differently:

    trim       keep the newest turns                     forgets everything old
    summarize  replace old turns with a short summary    keeps the gist, loses detail
    retrieve   fetch the old turns that look relevant    keeps detail, can miss

This exercise builds all three as functions with one shape,

    strategy(history, question) -> the messages to send

and compares them on the two things that matter: RECALL (can the bot still
answer questions about the conversation?) and COST (input tokens per question).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import numpy as np
import tiktoken
from langchain_core.language_models import BaseChatModel

from aicourse.llm import get_chat_model, get_embeddings

CONVERSATION = Path(__file__).resolve().parent.parent / "conversation.json"
SYSTEM = ("You are the Nimbus Coffee support assistant. Answer the question about this customer from the "
          "conversation you are given. If the conversation does not contain the answer, say you do not know.")
SUMMARY_PREFIX = "Summary of the earlier conversation: "
ENCODING = tiktoken.get_encoding("o200k_base")

Message = dict  # {"role": "user" | "assistant" | "system", "content": str}
Strategy = Callable[[list[Message], str], list[Message]]
Embedder = Callable[[list[str]], list[list[float]]]


# ------------------------------------------------------------------ cost
def count_tokens(messages: list[Message]) -> int:
    """Estimated tokens of a message list: the text of each message plus 4 for its role and separators."""
    return sum(len(ENCODING.encode(m["content"])) + 4 for m in messages)


# ------------------------------------------------------------------ strategy 0: everything
def full_history(history: list[Message], question: str) -> list[Message]:
    """The baseline: perfect recall, and the bill grows with every turn."""
    return list(history)


# ------------------------------------------------------------------ strategy 1: trim
def trim_recent(history: list[Message], max_tokens: int) -> list[Message]:
    """The newest messages that fit in max_tokens, in order, starting on a user message."""
    kept: list[Message] = []
    budget = max_tokens
    for message in reversed(history):
        cost = count_tokens([message])
        if cost > budget:
            break
        kept.append(message)
        budget -= cost
    kept.reverse()
    while kept and kept[0]["role"] != "user":  # never start on an answer whose question was cut
        kept.pop(0)
    return kept


# ------------------------------------------------------------------ strategy 2: summarize
def summarize(llm: BaseChatModel, messages: list[Message], max_words: int = 120) -> str:
    """One model call that condenses old turns. Facts about the customer matter more than chit-chat."""
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    return llm.invoke([
        ("system", f"Summarize this support conversation in at most {max_words} words. Keep every fact about the "
                   "customer: names, numbers, addresses, dates, preferences, allergies and promises made. "
                   "Leave out general coffee advice. No preamble."),
        ("user", transcript),
    ]).text.strip()


def summary_and_recent(history: list[Message], summary: str, keep_last: int = 4) -> list[Message]:
    """One summary message standing in for the old turns, then the last `keep_last` messages word for word."""
    recent = history[-keep_last:] if keep_last else []
    if len(history) <= keep_last:
        return list(history)  # nothing old to stand in for
    return [{"role": "system", "content": SUMMARY_PREFIX + summary}] + recent


# ------------------------------------------------------------------ strategy 3: retrieve
def pair_turns(history: list[Message]) -> list[list[Message]]:
    """Group the history into exchanges: [user message, assistant reply]. A question and its
    answer are retrieved together, because either one alone is half a fact."""
    pairs: list[list[Message]] = []
    for message in history:
        if message["role"] == "user" or not pairs:
            pairs.append([message])
        else:
            pairs[-1].append(message)
    return pairs


def cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    return float(va @ vb) / denom if denom else 0.0


class TurnIndex:
    """Embeds every exchange of a conversation ONCE, then finds the ones closest to a question."""

    def __init__(self, history: list[Message], embed: Embedder) -> None:
        self.pairs = pair_turns(history)
        self.embed = embed
        self.texts = ["\n".join(f"{m['role']}: {m['content']}" for m in pair) for pair in self.pairs]
        self.vectors = embed(self.texts) if self.texts else []

    def top(self, question: str, k: int) -> list[int]:
        """Positions of the k most similar exchanges, best first."""
        query = self.embed([question])[0]
        scores = [cosine(query, vector) for vector in self.vectors]
        return sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]


def retrieve_turns(index: TurnIndex, question: str, k: int = 3, keep_last: int = 1) -> list[Message]:
    """The k most relevant exchanges plus the last `keep_last` exchanges, in their original order."""
    chosen = set(index.top(question, k))
    chosen |= set(range(max(0, len(index.pairs) - keep_last), len(index.pairs)))
    return [message for i in sorted(chosen) for message in index.pairs[i]]  # chronological: old before new


# ------------------------------------------------------------------ measure
def ask(llm: BaseChatModel, context: list[Message], question: str) -> str:
    messages = [("system", SYSTEM)] + [(m["role"], m["content"]) for m in context] + [("user", question)]
    return llm.invoke(messages).text


def recalled(answer: str, keywords: list[str]) -> bool:
    return all(keyword.lower() in answer.lower() for keyword in keywords)


def evaluate(llm: BaseChatModel, strategy: Strategy, history: list[Message], probes: list[dict]) -> dict:
    """Run every probe question through one strategy. Returns recall, mean input tokens and the misses."""
    hits, tokens, missed = 0, 0, []
    for probe in probes:
        context = strategy(history, probe["question"])
        tokens += count_tokens(context)
        if recalled(ask(llm, context, probe["question"]), probe["expect_keywords"]):
            hits += 1
        else:
            missed.append(probe["question"])
    return {"recall": hits / len(probes), "tokens_per_question": round(tokens / len(probes)), "missed": missed}


def default_embedder() -> Embedder:
    embeddings = get_embeddings()
    return embeddings.embed_documents


def build_strategies(llm: BaseChatModel, history: list[Message], embed: Embedder,
                     budget: int = 400) -> dict[str, Strategy]:
    """The four strategies, ready to compare. Summary and index are built once per conversation."""
    summary = summarize(llm, history[:-4])
    index = TurnIndex(history, embed)
    return {
        "full history": full_history,
        f"trim ({budget} tok)": lambda h, q: trim_recent(h, budget),
        "summary + last 4": lambda h, q: summary_and_recent(h, summary, keep_last=4),
        "retrieve 3 + last": lambda h, q: retrieve_turns(index, q, k=3, keep_last=1),
    }


def main() -> None:
    data = json.loads(CONVERSATION.read_text(encoding="utf-8"))
    history, probes = data["turns"], data["probes"]
    llm = get_chat_model(temperature=0)
    print(f"The conversation: {len(history)} messages, {count_tokens(history)} tokens. {len(probes)} probe questions.\n")
    print(f"{'strategy':<20}{'recall':>8}{'tokens/question':>17}   missed")
    for name, strategy in build_strategies(llm, history, default_embedder()).items():
        result = evaluate(llm, strategy, history, probes)
        print(f"{name:<20}{result['recall']:>8.0%}{result['tokens_per_question']:>17}   "
              f"{'; '.join(q[:38] for q in result['missed']) or '-'}")
    print("\nSetup costs once per conversation: one summary call (reads the whole history), "
          f"one embedding call ({len(pair_turns(history))} exchanges).")


if __name__ == "__main__":
    main()
