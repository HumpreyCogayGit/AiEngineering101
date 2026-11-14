"""EXER039 checks. Run:  uv run python EXER039/check.py"""

import json
import re

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("memory_strategies.py")

DATA = json.loads(mod.CONVERSATION.read_text(encoding="utf-8"))
HISTORY, PROBES = DATA["turns"], DATA["probes"]


def msg(role, content):
    return {"role": role, "content": content}


VOCAB = ["order", "number", "allergy", "nut", "floor", "delivery", "address", "wholesale", "kilos", "month",
         "invoice", "email", "grinder", "friday", "roast", "refund", "wifi", "decaf", "shipping", "stars"]


def toy_embed(texts):
    """A tiny offline 'embedding': one dimension per vocabulary word. Enough to test the plumbing."""
    return [[float(len(re.findall(rf"\b{word}", text.lower()))) for word in VOCAB] + [0.01] for text in texts]


@checker.check("count_tokens() adds the text tokens and 4 per message")
def _():
    one = mod.count_tokens([msg("user", "hello world")])
    assert one == len(mod.ENCODING.encode("hello world")) + 4, one
    assert mod.count_tokens([msg("user", "hello world")] * 3) == 3 * one
    assert mod.count_tokens([]) == 0


@checker.check("trim_recent() keeps the newest messages that fit, in order, starting on a user message")
def _():
    history = [msg("user" if i % 2 == 0 else "assistant", f"message {i} " + "word " * 20) for i in range(20)]
    budget = 150
    kept = mod.trim_recent(history, budget)
    assert kept and kept[-1] is history[-1] or kept[-1] == history[-1], "the newest message must be kept"
    assert kept == history[-len(kept):], "kept messages must be the tail of the history, in order"
    assert mod.count_tokens(kept) <= budget, mod.count_tokens(kept)
    assert kept[0]["role"] == "user", "must not start on an assistant message"
    assert len(kept) < len(history)
    assert mod.trim_recent(history, 10_000) == history, "everything fits: nothing is dropped"


@checker.check("summary_and_recent() puts one summary message before the last turns")
def _():
    context = mod.summary_and_recent(HISTORY, "Rina, order 4471.", keep_last=4)
    assert len(context) == 5 and context[0]["role"] == "system", context[:1]
    assert context[0]["content"] == mod.SUMMARY_PREFIX + "Rina, order 4471."
    assert context[1:] == HISTORY[-4:]
    assert mod.summary_and_recent(HISTORY[:3], "unused", keep_last=4) == HISTORY[:3], "a short history needs no summary"


@checker.check("pair_turns() groups each question with its answer")
def _():
    pairs = mod.pair_turns(HISTORY)
    assert len(pairs) == len(HISTORY) // 2, len(pairs)
    assert all([m["role"] for m in pair] == ["user", "assistant"] for pair in pairs)
    assert [m for pair in pairs for m in pair] == HISTORY, "no message may be lost or reordered"
    assert mod.pair_turns([msg("user", "a"), msg("user", "b"), msg("assistant", "c")]) == [
        [msg("user", "a")], [msg("user", "b"), msg("assistant", "c")]]


@checker.check("retrieve_turns() returns the relevant exchange and the last one, oldest first")
def _():
    index = mod.TurnIndex(HISTORY, toy_embed)
    context = mod.retrieve_turns(index, "Which allergy does the customer have?", k=1, keep_last=1)
    assert len(context) == 4, [m["content"][:30] for m in context]
    assert "nut allergy" in context[0]["content"], context[0]["content"]
    assert context[2:] == HISTORY[-2:], "the last exchange is always included"
    positions = [HISTORY.index(m) for m in context]
    assert positions == sorted(positions), "exchanges must be in their original order"
    overlap = mod.retrieve_turns(index, "Which email should the invoice go to?", k=2, keep_last=2)
    assert len(overlap) == len({m["content"] for m in overlap}), "an exchange must not be included twice"


@checker.check("evaluate() reports recall, tokens per question and the misses")
def _():
    llm = fake_chat_model("The order number is 4471.")  # the same answer to everything
    probes = [{"question": "Order number?", "expect_keywords": ["4471"]},
              {"question": "Allergy?", "expect_keywords": ["nut"]}]
    result = mod.evaluate(llm, mod.full_history, HISTORY[:4], probes)
    assert result["recall"] == 0.5, result
    assert result["tokens_per_question"] == mod.count_tokens(HISTORY[:4]), result
    assert result["missed"] == ["Allergy?"], result
    sent = llm.received[0]
    assert len(sent) == 6 and sent[-1].content == "Order number?", "system + the context + the question are sent"


@checker.check("summarizing and retrieving recall more than trimming, for far fewer tokens than the full history  [live API]")
def _():
    llm = get_chat_model(temperature=0)
    strategies = mod.build_strategies(llm, HISTORY, mod.default_embedder())
    results = {name: mod.evaluate(llm, strategy, HISTORY, PROBES) for name, strategy in strategies.items()}
    full, trim, summary, retrieve = results.values()
    assert full["recall"] >= 5 / 6, results
    assert trim["recall"] < full["recall"], "a 400-token window cannot hold the early facts"
    assert summary["recall"] > trim["recall"] and retrieve["recall"] > trim["recall"], results
    assert summary["tokens_per_question"] < full["tokens_per_question"] / 2, results
    assert retrieve["tokens_per_question"] < full["tokens_per_question"] / 2, results


checker.run()
