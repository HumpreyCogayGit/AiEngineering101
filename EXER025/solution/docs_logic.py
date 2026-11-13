"""EXER025 — logic for "Chat With Your Docs" (reference solution)."""

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
    """Uploaded files arrive as bytes; reuse the file loaders via a temp file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / Path(name).name
        path.write_bytes(data)
        return [d for d in load_file(path) if d.page_content.strip()]


def build_index(docs: list[Document], embeddings: Embeddings) -> Chroma:
    """An in-memory Chroma collection, private to this browser session."""
    client = chromadb.EphemeralClient(settings=chromadb.Settings(anonymized_telemetry=False))
    store = Chroma(
        client=client,
        collection_name=f"session-{uuid.uuid4().hex[:12]}",
        embedding_function=embeddings,
        collection_metadata={"hnsw:space": "cosine"},
    )
    store.add_documents(split_documents(docs))
    return store


def to_messages(history: list[dict]) -> list:
    return [HumanMessage(m["content"]) if m["role"] == "user" else AIMessage(m["content"]) for m in history]


CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Rewrite the user's last question as a standalone question that can be understood "
               "without the conversation. Keep it short. Output only the question."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])


def condense_question(llm: BaseChatModel, history: list[dict], question: str) -> str:
    """'How much is it?' after talking about cold brew -> 'How much is the Cold Brew Bottle?'"""
    if not history:
        return question
    chain = CONDENSE_PROMPT | llm | StrOutputParser()
    return chain.invoke({"history": to_messages(history[-6:]), "question": question}).strip()


ANSWER_PROMPT = ChatPromptTemplate.from_messages([("system", RAG_SYSTEM_PROMPT), ("human", "{question}")])


def answer(llm: BaseChatModel, store: Chroma, history: list[dict], question: str, k: int = 4) -> dict:
    standalone = condense_question(llm, history, question)
    docs = store.similarity_search(standalone, k=k)
    chain = ANSWER_PROMPT | llm | StrOutputParser()
    text = chain.invoke({"context": format_docs(docs), "question": standalone})
    return {"answer": text, "docs": docs, "standalone": standalone}
