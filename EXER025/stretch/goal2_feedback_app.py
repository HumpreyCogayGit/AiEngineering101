"""EXER025 stretch goal 2 — thumbs up/down per answer, written to a file.

    uv run streamlit run EXER025/stretch/goal2_feedback_app.py
    cat EXER025/stretch/output/feedback.jsonl

Each rating is stored with everything needed to act on it later: the
question, the standalone query that was searched, the sources and the answer.
A thumbs-down with its sources tells you whether retrieval or generation
failed, and it is a ready-made test case for the golden set (EXER024).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from aicourse.llm import get_chat_model, get_embeddings
from aicourse.rag import KB_DIR
from aicourse.stretch import solution_module

logic = solution_module(__file__, "docs_logic.py")
FEEDBACK_FILE = Path(__file__).resolve().parent / "output" / "feedback.jsonl"


def save_feedback(entry: dict, rating: str, path: Path = FEEDBACK_FILE) -> None:
    """Append one rating as a JSON line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "rating": rating,
              "question": entry["question"], "standalone": entry["standalone"],
              "sources": entry["sources"], "answer": entry["content"]}
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


st.set_page_config(page_title="Chat With Your Docs", page_icon="📚", layout="wide")
st.title("📚 Chat With Your Docs")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "store" not in st.session_state:
    st.session_state.store = None

with st.sidebar:
    st.header("Documents")
    if st.button("Build index from the sample documents", type="primary"):
        docs = []
        for path in sorted(KB_DIR.iterdir()):
            docs += logic.load_uploaded(path.name, path.read_bytes())
        with st.spinner(f"Embedding {len(docs)} documents..."):
            st.session_state.store = logic.build_index(docs, get_embeddings())
        st.session_state.messages = []
    rated = sum("rating" in m for m in st.session_state.messages)
    st.caption(f"{rated} answer(s) rated in this session")

# Draw the conversation. Each assistant message gets its own feedback widget.
for index, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant":
            choice = st.feedback("thumbs", key=f"feedback-{index}")  # None, 0 (down) or 1 (up)
            if choice is not None and "rating" not in m:  # store each answer's rating once
                m["rating"] = "up" if choice == 1 else "down"
                save_feedback(m, m["rating"])
                st.toast("Thanks, feedback saved.")

if st.session_state.store is None:
    st.info("Click **Build index from the sample documents** in the sidebar to start.")
elif question := st.chat_input("Ask about your documents"):
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
    with st.spinner("Searching..."):
        result = logic.answer(get_chat_model(temperature=0), st.session_state.store, history, question)
    st.session_state.messages += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": result["answer"], "question": question,
         "standalone": result["standalone"],
         "sources": [d.metadata.get("source") for d in result["docs"]]},
    ]
    st.rerun()  # redraw through the loop above, so the new answer gets its feedback widget
