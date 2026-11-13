"""EXER015 — logic for the Streamlit chat app (reference solution).

Keeping the logic out of app.py makes it testable without a browser.
"""

from __future__ import annotations

from typing import Iterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


def to_langchain_messages(history: list[dict], system_prompt: str) -> list[BaseMessage]:
    """Streamlit history [{"role": "user"|"assistant", "content": str}] -> LangChain messages."""
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]
    for item in history:
        cls = HumanMessage if item["role"] == "user" else AIMessage
        messages.append(cls(content=item["content"]))
    return messages


def stream_answer(llm: BaseChatModel, history: list[dict], system_prompt: str) -> Iterator[str]:
    """Yield the answer as text pieces — st.write_stream() consumes this directly."""
    for chunk in llm.stream(to_langchain_messages(history, system_prompt)):
        if chunk.text:
            yield chunk.text
