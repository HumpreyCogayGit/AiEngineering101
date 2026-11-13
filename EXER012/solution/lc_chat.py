"""EXER012 — LangChain Chat Models (reference solution).

LangChain wraps every provider behind one interface (`BaseChatModel`) with
three core methods: invoke (one answer), stream (pieces) and batch (many).
Messages become typed objects: SystemMessage, HumanMessage, AIMessage.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from aicourse.llm import model_params
from aicourse.settings import get_settings


def make_llm(temperature: float = 0.7) -> ChatOpenAI:
    """Build the chat model by hand (later: aicourse.llm.get_chat_model())."""
    s = get_settings()
    return ChatOpenAI(
        model=s.chat_model,
        base_url=s.base_url,
        api_key=s.api_key.get_secret_value(),
        timeout=s.request_timeout,
        **model_params(temperature=temperature),  # left out for models that reject it
    )


def ask(llm: BaseChatModel, question: str, system: str | None = None) -> str:
    messages: list[BaseMessage] = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=question))
    return llm.invoke(messages).text  # .text is always a string; .content may be a list of blocks


def batch_ask(llm: BaseChatModel, questions: list[str]) -> list[str]:
    """Run several independent questions in parallel with .batch()."""
    return [m.text for m in llm.batch(questions)]


def stream_print(llm: BaseChatModel, question: str) -> str:
    parts = []
    for chunk in llm.stream(question):
        print(chunk.text, end="", flush=True)
        parts.append(chunk.text)
    print()
    return "".join(parts)


class LCConversation:
    """The EXER005 chatbot, now with LangChain message objects."""

    def __init__(self, llm: BaseChatModel, system: str) -> None:
        self.llm = llm
        self.history: list[BaseMessage] = [SystemMessage(content=system)]

    def send(self, text: str) -> str:
        self.history.append(HumanMessage(content=text))
        reply = self.llm.invoke(self.history)
        self.history.append(AIMessage(content=reply.text))
        return reply.text


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
