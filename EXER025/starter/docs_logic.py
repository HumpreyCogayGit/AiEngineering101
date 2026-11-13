"""EXER025 — logic for "Chat With Your Docs".

Complete the TODOs here first, then app.py.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from aicourse.rag import RAG_SYSTEM_PROMPT, format_docs, load_file, split_documents

SUPPORTED = ["md", "txt", "html", "pdf"]


def load_uploaded(name: str, data: bytes) -> list[Document]:
    """Uploaded files arrive as bytes. Write them to a temp file and reuse the loaders.

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / Path(name).name      # Path(name).name strips any "../" tricks
        path.write_bytes(data)
        return [d for d in load_file(path) if d.page_content.strip()]
    """
    # TODO
    raise NotImplementedError("load_uploaded")


def build_index(docs: list[Document], embeddings: Embeddings) -> Chroma:
    """An IN-MEMORY Chroma collection, private to this browser session.

    client = chromadb.EphemeralClient(settings=chromadb.Settings(anonymized_telemetry=False))
    Use a unique collection name (e.g. f"session-{uuid.uuid4().hex[:12]}") so two
    sessions never share data. Add split_documents(docs) to it.
    """
    # TODO
    raise NotImplementedError("build_index")


def to_messages(history: list[dict]) -> list:
    return [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]


CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the user's last question as a standalone question that can be understood "
               "without the conversation. Keep it short. Output only the question."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])


def condense_question(llm: BaseChatModel, history: list[dict], question: str) -> str:
    """Follow-up questions like "How much is it?" can't be searched on their own.

    - no history -> return the question unchanged (no LLM call!)
    - otherwise  -> (CONDENSE_PROMPT | llm | StrOutputParser()).invoke(
                        {"history": to_messages(history[-6:]), "question": question}).strip()
    """
    # TODO
    raise NotImplementedError("condense_question")


ANSWER_PROMPT = ChatPromptTemplate.from_messages([("system", RAG_SYSTEM_PROMPT), ("human", "{question}")])


def answer(llm: BaseChatModel, store: Chroma, history: list[dict], question: str, k: int = 4) -> dict:
    """Conversational RAG.

    1. standalone = condense_question(...)
    2. docs = store.similarity_search(standalone, k=k)
    3. text = (ANSWER_PROMPT | llm | StrOutputParser()).invoke({"context": format_docs(docs), "question": standalone})
    4. return {"answer": text, "docs": docs, "standalone": standalone}
    """
    # TODO
    raise NotImplementedError("answer")
