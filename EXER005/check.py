"""EXER005 checks. Run:  uv run python EXER005/check.py"""

from aicourse.check import Checker
from aicourse.fakes import FakeClient
from aicourse.llm import get_openai_client

checker = Checker(__file__)
mod = checker.load("chatbot.py")


@checker.check("Conversation starts with exactly one system message")
def _():
    c = mod.Conversation("Be nice.")
    assert c.messages == [{"role": "system", "content": "Be nice."}], c.messages


@checker.check("add_user / add_assistant append messages with the right roles")
def _():
    c = mod.Conversation("S")
    c.add_user("hi")
    c.add_assistant("hello")
    assert [m["role"] for m in c.messages] == ["system", "user", "assistant"]


@checker.check("reset() keeps only the system prompt")
def _():
    c = mod.Conversation("S")
    c.add_user("hi")
    c.reset()
    assert c.messages == [{"role": "system", "content": "S"}]


@checker.check("chat_turn() stores the reply and returns it")
def _():
    c = mod.Conversation("S")
    reply = mod.chat_turn(FakeClient(["Hi! I'm a bot."]), c, "hello")
    assert reply == "Hi! I'm a bot."
    assert c.messages[-1] == {"role": "assistant", "content": "Hi! I'm a bot."}


@checker.check("the SECOND turn sends the whole history (that is the memory)")
def _():
    fake = FakeClient(["first answer", "second answer"])
    c = mod.Conversation("S")
    mod.chat_turn(fake, c, "my name is Ada")
    mod.chat_turn(fake, c, "what is my name?")
    sent = fake.calls[1]["messages"]
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"], sent
    assert sent[1]["content"] == "my name is Ada"


@checker.check("the bot remembers your name across turns  [live API]")
def _():
    c = mod.Conversation("You are a helpful assistant.")
    client = get_openai_client()
    mod.chat_turn(client, c, "Hi, my name is Zephyrine. Just say hi back.")
    reply = mod.chat_turn(client, c, "What is my name? Reply with the name only.")
    assert "zephyrine" in reply.lower(), reply


checker.run()
