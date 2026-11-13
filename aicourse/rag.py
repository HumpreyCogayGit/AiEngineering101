"""Shared RAG building blocks.

You build each of these yourself in EXER019 – EXER021. Later exercises
import them so they can focus on the new concept:

    from aicourse.rag import get_vector_store
    store = get_vector_store()                 # builds the index on first use
    docs = store.similarity_search("refund policy", k=3)
"""

from __future__ import annotations

import hashlib
import re
import threading
from pathlib import Path

from langchain_core.documents import Document

from aicourse.settings import DATA_DIR, get_settings

KB_DIR = DATA_DIR / "knowledge_base"


# ------------------------------------------------------------------ loading
def load_file(path: Path) -> list[Document]:
    """Load one .md / .txt / .html / .pdf file into Documents (one per PDF page)."""
    suffix = path.suffix.lower()
    if suffix in (".md", ".txt"):
        return [Document(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name})]
    if suffix in (".html", ".htm"):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = re.sub(r"\n\s*\n+", "\n\n", soup.get_text("\n")).strip()
        title = soup.title.get_text(strip=True) if soup.title else path.stem
        return [Document(page_content=text, metadata={"source": path.name, "title": title})]
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        return [
            Document(page_content=page.extract_text() or "", metadata={"source": path.name, "page": i + 1})
            for i, page in enumerate(reader.pages)
        ]
    return []


def load_knowledge_base(directory: Path = KB_DIR) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(directory.iterdir()):
        docs.extend(load_file(path))
    return [d for d in docs if d.page_content.strip()]


# ------------------------------------------------------------------ chunking
def split_documents(docs: list[Document], chunk_size: int = 600, chunk_overlap: int = 100) -> list[Document]:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


def chunk_id(doc: Document) -> str:
    """Stable id from content + source, so re-ingesting never creates duplicates."""
    key = f"{doc.metadata.get('source')}::{doc.page_content}"
    return hashlib.sha256(key.encode()).hexdigest()[:32]


# ------------------------------------------------------------------ vector store
def default_collection_name() -> str:
    # Include the embedding deployment: vectors from different models are not comparable.
    dep = re.sub(r"[^a-zA-Z0-9_-]", "-", get_settings().embedding_deployment)
    return f"nimbus_kb_{dep}"[:60]


_STORES: dict[tuple[str, str], object] = {}
_STORE_LOCK = threading.Lock()


def get_vector_store(collection_name: str | None = None, embeddings=None, rebuild: bool = False):
    """Persistent Chroma store with the knowledge base, built on first use.

    The store is created once per process and then reused. Agents run several
    tool calls at the same time (parallel tool calls, each in its own thread),
    and opening the same Chroma folder from two threads at once fails with
    "Could not connect to tenant default_tenant".
    """
    import chromadb
    from langchain_chroma import Chroma

    from aicourse.llm import get_embeddings

    settings = get_settings()
    name = collection_name or default_collection_name()
    key = (str(settings.chroma_path), name)
    with _STORE_LOCK:
        if embeddings is None and not rebuild and key in _STORES:
            return _STORES[key]
        client = chromadb.PersistentClient(
            path=str(settings.chroma_path),
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
        if rebuild:
            try:
                client.delete_collection(name)
            except Exception:
                pass
        store = Chroma(
            client=client,
            collection_name=name,
            embedding_function=embeddings or get_embeddings(),
            collection_metadata={"hnsw:space": "cosine"},
        )
        if store._collection.count() == 0:
            chunks = split_documents(load_knowledge_base())
            store.add_documents(chunks, ids=[chunk_id(c) for c in chunks])
        if embeddings is None:
            _STORES[key] = store
        return store


def format_docs(docs: list[Document]) -> str:
    """Number the chunks so the model can cite them as [1], [2], ..."""
    return "\n\n".join(
        f"[{i}] (source: {d.metadata.get('source', '?')})\n{d.page_content}" for i, d in enumerate(docs, 1)
    )


# ------------------------------------------------------------------ the RAG chain (EXER022)
NOT_FOUND = "I don't know based on the available documents."

RAG_SYSTEM_PROMPT = (
    "You are the customer assistant of Nimbus Coffee Co.\n"
    "Answer the question using ONLY the numbered context passages below.\n"
    "Rules:\n"
    "- Cite the passages you used with their number in square brackets, e.g. [1] or [2][3].\n"
    f"- If the answer is not in the context, reply exactly: {NOT_FOUND}\n"
    "- Never use outside knowledge. Be concise.\n\n"
    "Context:\n{context}"
)


def build_rag_chain(retriever=None, llm=None):
    """question (str) -> {"question", "docs", "answer"}  (the EXER022 solution)."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough

    from aicourse.llm import get_chat_model

    retriever = retriever or get_vector_store().as_retriever(search_kwargs={"k": 4})
    llm = llm or get_chat_model(temperature=0)
    prompt = ChatPromptTemplate.from_messages([("system", RAG_SYSTEM_PROMPT), ("human", "{question}")])
    generate = (
        RunnableLambda(lambda x: {"context": format_docs(x["docs"]), "question": x["question"]})
        | prompt
        | llm
        | StrOutputParser()
    )
    return RunnableParallel(docs=retriever, question=RunnablePassthrough()) | RunnablePassthrough.assign(
        answer=generate
    )
