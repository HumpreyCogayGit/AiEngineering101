"""EXER015 — logic for the Streamlit chat app.

Keeping the logic out of app.py makes it testable without a browser.
"""

from __future__ import annotations

from typing import Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


def to_langchain_messages(history: list[dict], system_prompt: str) -> list[BaseMessage]:
    """Streamlit history -> LangChain messages.

    history looks like [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    Return [SystemMessage(system_prompt), HumanMessage(...), AIMessage(...), ...]
    """
    # TODO
    raise NotImplementedError("to_langchain_messages")


def stream_answer(llm: BaseChatModel, history: list[dict], system_prompt: str) -> Iterator[str]:
    """Yield the answer as text pieces — st.write_stream() consumes this directly.

    for chunk in llm.stream(<the converted messages>): yield chunk.text (skip empty ones)
    """
    # TODO
    raise NotImplementedError("stream_answer")
