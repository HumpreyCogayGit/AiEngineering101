"""EXER012 — LangChain Chat Models.

LangChain wraps every provider behind one interface (`BaseChatModel`) with
three core methods: invoke (one answer), stream (pieces) and batch (many).
Messages become typed objects: SystemMessage, HumanMessage, AIMessage.

    uv run python EXER012/starter/lc_chat.py
    uv run python EXER012/check.py
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from aicourse.llm import model_params
from aicourse.settings import get_settings


def make_llm(temperature: float = 0.7) -> ChatOpenAI:
    """Build the chat model by hand.

    ChatOpenAI(model=<chat deployment>, base_url=..., api_key=<the secret value>,
               timeout=..., **model_params(temperature=temperature))
    model_params() leaves temperature out for models that reject it (gpt-5 family).
    (After this exercise you can use aicourse.llm.get_chat_model() instead.)
    """
    # TODO
    raise NotImplementedError("make_llm")


def ask(llm: BaseChatModel, question: str, system: str | None = None) -> str:
    """Build [SystemMessage? , HumanMessage], call llm.invoke(messages), return .text"""
    # TODO
    raise NotImplementedError("ask")


def batch_ask(llm: BaseChatModel, questions: list[str]) -> list[str]:
    """Run several independent questions in parallel with llm.batch(questions).

    Every runnable accepts a plain string as input — LangChain turns it into a HumanMessage.
    Return the list of reply texts.
    """
    # TODO
    raise NotImplementedError("batch_ask")


def stream_print(llm: BaseChatModel, question: str) -> str:
    """for chunk in llm.stream(question): print chunk.text without newline.
    Return the full text."""
    # TODO
    raise NotImplementedError("stream_print")


class LCConversation:
    """The EXER005 chatbot, now with LangChain message objects."""

    def __init__(self, llm: BaseChatModel, system: str) -> None:
        self.llm = llm
        self.history: list[BaseMessage] = [SystemMessage(content=system)]

    def send(self, text: str) -> str:
        """Append a HumanMessage, invoke with the whole history,
        append the reply as an AIMessage, return the reply text."""
        # TODO
        raise NotImplementedError("LCConversation.send")


def main() -> None:
    llm = make_llm()
    print(ask(llm, "What is LangChain in one sentence?", system="You are concise."))

    reply = llm.invoke("Say hi")
    print("\nAn AIMessage carries metadata too:")
    print("  type          :", type(reply).__name__)
    print("  usage_metadata:", reply.usage_metadata)

    print("\nBatch:", batch_ask(llm, ["2+2? digits only", "Capital of Italy? one word", "Opposite of hot? one word"]))

    print("\nStream: ", end="")
    stream_print(llm, "Name five planets, comma separated.")

    convo = LCConversation(llm, "You are a helpful assistant.")
    convo.send("My favourite colour is teal.")
    print("\nMemory:", convo.send("What's my favourite colour?"))


if __name__ == "__main__":
    main()
