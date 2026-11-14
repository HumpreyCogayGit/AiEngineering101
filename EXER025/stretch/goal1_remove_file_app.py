"""EXER025 stretch goal 1 — let the user remove one uploaded file from the index.

    uv run streamlit run EXER025/stretch/goal1_remove_file_app.py

The sidebar lists the indexed files, each with a Remove button. Removing a
file deletes its chunks from the session's index (see remove_file.py) without
rebuilding or re-embedding anything else.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))  # for remove_file.py next to this file

from aicourse.llm import get_chat_model, get_embeddings
from aicourse.rag import KB_DIR
from aicourse.stretch import solution_module
from remove_file import indexed_files, remove_file

logic = solution_module(__file__, "docs_logic.py")

st.set_page_config(page_title="Chat With Your Docs", page_icon="📚", layout="wide")
st.title("📚 Chat With Your Docs")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "store" not in st.session_state:
    st.session_state.store = None

with st.sidebar:
    st.header("Documents")
    uploads = st.file_uploader("Upload files", type=logic.SUPPORTED, accept_multiple_files=True)
    use_sample = st.checkbox("Include the Nimbus Coffee sample documents", value=not uploads)
    if st.button("Build index", type="primary"):
        docs = []
        for f in uploads or []:
            docs += logic.load_uploaded(f.name, f.getvalue())
        if use_sample:
            for path in sorted(KB_DIR.iterdir()):
                docs += logic.load_uploaded(path.name, path.read_bytes())
        if not docs:
            st.warning("Upload a file or tick the sample documents first.")
        else:
            with st.spinner(f"Embedding {len(docs)} documents..."):
                st.session_state.store = logic.build_index(docs, get_embeddings())
            st.session_state.messages = []

    if st.session_state.store is not None:
        files = indexed_files(st.session_state.store)  # read from the index itself: always in step
        st.subheader(f"Indexed files ({len(files)})")
        for name in files:
            left, right = st.columns([3, 1])
            left.write(name)
            if right.button("Remove", key=f"remove-{name}"):
                removed = remove_file(st.session_state.store, name)
                st.toast(f"Removed {name} ({removed} chunks)")
                st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

store = st.session_state.store
if store is None:
    st.info("Add documents in the sidebar and click **Build index** to start.")
elif not indexed_files(store):
    st.info("The index is empty. Build it again to continue.")
elif question := st.chat_input("Ask about your documents"):
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            result = logic.answer(get_chat_model(temperature=0), store, st.session_state.messages, question)
        st.markdown(result["answer"])
        with st.expander("Sources"):
            for i, d in enumerate(result["docs"], 1):
                st.markdown(f"**[{i}] {d.metadata.get('source')}**")
                st.text(d.page_content[:400])
    st.session_state.messages += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": result["answer"]},
    ]
