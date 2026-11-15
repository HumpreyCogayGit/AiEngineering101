"""EXER025 transfer task — reference answer: RAG over a document collection you have never seen.

    uv run python EXER025/transfer/reference_harbor_rag.py

Read this only after you have built your own. Nothing here is Nimbus-specific:
the loaders, the splitter and the evaluation are the Module 4 ones, pointed at
three Harbor Bikes documents (Markdown and HTML) and ten golden questions, two
of which the documents cannot answer.

What it reports, and why each number is separate (EXER024):
- hit rate      did retrieval find the right document?             (code)
- MRR           how high was it ranked?                             (code)
- correctness   does the answer contain the key fact?               (code: a keyword)
- refusal       does it say it doesn't know when it should?         (code)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate

from aicourse.llm import get_chat_model, get_embeddings
from aicourse.rag import chunk_id, format_docs, load_file, split_documents

HERE = Path(__file__).resolve().parent
NOT_FOUND = "I don't know based on the Harbor Bikes documents."
PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You answer questions for Harbor Bikes, a bike rental company in Iloilo City.\n"
               "Use ONLY the numbered passages. Cite them like [1].\n"
               f"If the passages do not contain the answer, reply exactly: {NOT_FOUND}\n\nPassages:\n{{context}}"),
    ("human", "{question}"),
])


def build_store() -> Chroma:
    docs = [d for path in sorted((HERE / "harbor_docs").iterdir()) for d in load_file(path)]
    chunks = split_documents(docs, chunk_size=400, chunk_overlap=60)
    store = Chroma(client=chromadb.EphemeralClient(settings=chromadb.Settings(anonymized_telemetry=False)),
                   collection_name="harbor", embedding_function=get_embeddings(),
                   collection_metadata={"hnsw:space": "cosine"})
    store.add_documents(chunks, ids=[chunk_id(c) for c in chunks])
    print(f"Indexed {len(docs)} documents as {len(chunks)} chunks.\n")
    return store


def normalize(text: str) -> str:
    return re.sub(r"[,₱]", "", text.lower().replace("’", "'"))


def main() -> None:
    store, llm = build_store(), get_chat_model(temperature=0)
    rows = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    hits, rr, correct, refused, answerable = 0, 0.0, 0, 0, 0
    for row in rows:
        docs = store.similarity_search(row["question"], k=3)
        sources = [d.metadata["source"] for d in docs]
        answer = (PROMPT | llm).invoke({"context": format_docs(docs), "question": row["question"]}).text
        said_no = "don't know" in normalize(answer)
        if row["expected_source"] is None:
            refused += said_no
            verdict = "ok  " if said_no else "MISS"
        else:
            answerable += 1
            hit = row["expected_source"] in sources
            hits += hit
            rr += 1 / (sources.index(row["expected_source"]) + 1) if hit else 0
            good = all(normalize(k) in normalize(answer) for k in row["keywords"]) and not said_no
            correct += good
            verdict = "ok  " if hit and good else "MISS"
        print(f"{verdict} {row['question'][:56]:<56} {', '.join(sources)}")
        print(f"     {answer.strip()[:110]}")
    unanswerable = len(rows) - answerable
    print(f"\nhit rate    {hits}/{answerable}   MRR {rr / answerable:.2f}")
    print(f"correctness {correct}/{answerable}")
    print(f"refusal     {refused}/{unanswerable}")


if __name__ == "__main__":
    main()
