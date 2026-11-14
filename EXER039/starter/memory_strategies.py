"""EXER039 — Conversation Memory Strategies (starter).

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
    """Estimated tokens of a message list.

    For each message: len(ENCODING.encode(message["content"])) + 4
    (the 4 stands for the role and the separators around a message).
    """
    # TODO
    raise NotImplementedError("count_tokens")


# ------------------------------------------------------------------ strategy 0: everything
def full_history(history: list[Message], question: str) -> list[Message]:
    """The baseline: perfect recall, and the bill grows with every turn."""
    return list(history)


# ------------------------------------------------------------------ strategy 1: trim
def trim_recent(history: list[Message], max_tokens: int) -> list[Message]:
    """The newest messages that fit in max_tokens, in their original order.

    1. Walk the history from the END (reversed). Keep a message while its cost, count_tokens([message]),
       still fits in the remaining budget; stop at the first one that does not fit.
    2. Put the kept messages back in chronological order.
    3. Drop messages from the FRONT until the first one is a user message: an assistant answer
       whose question was cut off makes no sense to the model.
    """
    # TODO
    raise NotImplementedError("trim_recent")


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
    """One summary message standing in for the old turns, then the last `keep_last` messages word for word.

    - If the history has keep_last messages or fewer, return a copy of it: nothing is old yet.
    - Otherwise return [{"role": "system", "content": SUMMARY_PREFIX + summary}] + the last keep_last messages.
    The summary text is passed in: it is written ONCE per conversation (see build_strategies), not per question.
    """
    # TODO
    raise NotImplementedError("summary_and_recent")


# ------------------------------------------------------------------ strategy 3: retrieve
def pair_turns(history: list[Message]) -> list[list[Message]]:
    """Group the history into exchanges: [[user message, assistant reply], ...].

    A user message starts a new exchange; any other message joins the current one.
    (If the history starts with an assistant message, that message starts the first exchange.)
    A question and its answer are retrieved together, because either one alone is half a fact.
    """
    # TODO
    raise NotImplementedError("pair_turns")


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
    """The k most relevant exchanges plus the last `keep_last` exchanges, in their ORIGINAL order.

    1. index.top(question, k) gives the positions of the k most similar exchanges.
    2. Add the positions of the last keep_last exchanges (the user is probably still talking about them).
    3. A position may be in both: use a set.
    4. Return the messages of those exchanges sorted by position, oldest first, as one flat list.
       index.pairs[i] is the list of messages of exchange i.
    """
    # TODO
    raise NotImplementedError("retrieve_turns")


# ------------------------------------------------------------------ measure
def ask(llm: BaseChatModel, context: list[Message], question: str) -> str:
    messages = [("system", SYSTEM)] + [(m["role"], m["content"]) for m in context] + [("user", question)]
    return llm.invoke(messages).text


def recalled(answer: str, keywords: list[str]) -> bool:
    return all(keyword.lower() in answer.lower() for keyword in keywords)


def evaluate(llm: BaseChatModel, strategy: Strategy, history: list[Message], probes: list[dict]) -> dict:
    """Run every probe question through one strategy.

    For each probe: context = strategy(history, probe["question"]); add count_tokens(context) to the
    total; answer = ask(llm, context, probe["question"]); it is a hit when
    recalled(answer, probe["expect_keywords"]).
    Return {"recall": hits / number of probes,
            "tokens_per_question": round(total tokens / number of probes),
            "missed": [the questions that were not recalled]}.
    """
    # TODO
    raise NotImplementedError("evaluate")


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
