"""EXER012 checks. Run:  uv run python EXER012/check.py"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model

checker = Checker(__file__)
mod = checker.load("lc_chat.py")


@checker.check("make_llm() returns a ChatOpenAI for your deployment")
def _():
    llm = mod.make_llm(temperature=0.1)
    assert isinstance(llm, ChatOpenAI)
    # LangChain itself drops temperature for reasoning models (gpt-5 family): None is fine there.
    assert llm.temperature in (0.1, None), llm.temperature
    assert str(llm.openai_api_base).endswith("/openai/v1/"), llm.openai_api_base


@checker.check("ask() sends SystemMessage + HumanMessage and returns text")
def _():
    llm = fake_chat_model("Paris")
    assert mod.ask(llm, "Capital of France?", system="Be brief") == "Paris"
    sent = llm.received[0]
    assert isinstance(sent[0], SystemMessage) and isinstance(sent[1], HumanMessage)


@checker.check("ask() without a system prompt sends only the HumanMessage")
def _():
    llm = fake_chat_model("ok")
    mod.ask(llm, "hi")
    assert len(llm.received[0]) == 1


@checker.check("answers are read with .text: a model that returns content BLOCKS still gives a string")
def _():
    blocks = AIMessage(content=[{"type": "text", "text": "Paris"}])  # what reasoning models return
    assert mod.ask(fake_chat_model(blocks), "Capital of France?") == "Paris", "use .text, not .content"
    assert mod.batch_ask(fake_chat_model(blocks), ["q1", "q2"]) == ["Paris", "Paris"], "use .text in batch_ask"
    convo = mod.LCConversation(fake_chat_model(blocks), system="Be brief")
    assert convo.send("Capital of France?") == "Paris", "use .text in LCConversation.send"


@checker.check("batch_ask() returns one answer per question")
def _():
    assert mod.batch_ask(fake_chat_model("a"), ["q1", "q2", "q3"]) == ["a", "a", "a"]


@checker.check("stream_print() returns the full streamed text")
def _():
    assert mod.stream_print(fake_chat_model("hello streaming world"), "x") == "hello streaming world"


@checker.check("LCConversation keeps a typed history")
def _():
    convo = mod.LCConversation(fake_chat_model("first", "second"), "S")
    convo.send("one")
    assert convo.send("two") == "second"
    types = [type(m) for m in convo.history]
    assert types == [SystemMessage, HumanMessage, AIMessage, HumanMessage, AIMessage], types


@checker.check("make_llm() talks to your deployment  [live API]")
def _():
    reply = mod.make_llm(0).invoke("Reply with the word: ready")
    assert isinstance(reply, AIMessage) and reply.text


checker.run()
