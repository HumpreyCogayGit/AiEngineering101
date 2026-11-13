"""EXER028 checks (offline, fake model). Run:  uv run python EXER028/check.py"""

import tempfile
from pathlib import Path

from langgraph.store.memory import InMemoryStore

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model

checker = Checker(__file__)
mod = checker.load("memory_bot.py")
NO_FACTS = mod.MemoryUpdate(facts=[])


def bot(*replies, facts=None, **kw):
    llm = fake_chat_model(*replies or ("ok",), structured=[facts or NO_FACTS])
    return mod.build_chatbot(llm, **kw), llm


def human_texts(messages):
    return [m.content for m in messages if m.type == "human"]


@checker.check("the same thread remembers earlier messages")
def _():
    graph, llm = bot()
    mod.send(graph, "My name is Bea", "t1")
    mod.send(graph, "What's my name?", "t1")
    assert human_texts(llm.received[-2]) == ["My name is Bea", "What's my name?"], "history was not sent"


@checker.check("different threads are isolated")
def _():
    graph, llm = bot()
    mod.send(graph, "My name is Bea", "t1")
    mod.send(graph, "What's my name?", "t2")
    assert human_texts(llm.received[-2]) == ["What's my name?"]


@checker.check("SQLite checkpoints survive a 'restart' (a brand-new graph)")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "mem.sqlite"
        graph1, _ = bot(checkpointer=mod.sqlite_checkpointer(db))
        mod.send(graph1, "Remember the word pineapple", "persist")
        graph2, _ = bot(checkpointer=mod.sqlite_checkpointer(db))
        assert human_texts(mod.history(graph2, "persist")) == ["Remember the word pineapple"]


@checker.check("long-term facts are stored per user and reach new threads")
def _():
    store = InMemoryStore()
    graph, llm = bot(facts=mod.MemoryUpdate(facts=["Allergic to dairy"]), store=store)
    mod.send(graph, "I'm allergic to dairy", "thread-a", user_id="bea")
    assert mod.recall(store, "bea") == ["Allergic to dairy"]
    assert mod.recall(store, "someone-else") == []
    mod.send(graph, "Suggest a drink", "thread-b", user_id="bea")
    system_prompt = llm.received[-2][0].content
    assert "Allergic to dairy" in system_prompt, system_prompt


@checker.check("facts are not stored twice")
def _():
    store = InMemoryStore()
    graph, _ = bot(facts=mod.MemoryUpdate(facts=["Likes oat milk"]), store=store)
    mod.send(graph, "I like oat milk", "t", user_id="u")
    mod.send(graph, "I really like oat milk", "t", user_id="u")
    assert mod.recall(store, "u") == ["Likes oat milk"]


@checker.check("only the last MAX_HISTORY messages are sent to the model")
def _():
    graph, llm = bot()
    for i in range(15):
        mod.send(graph, f"message {i}", "long")
    sent = llm.received[-2]
    assert len(sent) - 1 <= mod.MAX_HISTORY, f"{len(sent) - 1} messages sent"
    assert len(mod.history(graph, "long")) == 30, "the checkpoint itself should keep everything"


checker.run()
