"""EXER025 — Chat With Your Docs.

    uv run streamlit run EXER025/starter/app.py

Complete docs_logic.py first, then the TODOs below.
"""

import streamlit as st

from aicourse.llm import get_chat_model, get_embeddings
from aicourse.rag import KB_DIR
from docs_logic import SUPPORTED, answer, build_index, load_uploaded

st.set_page_config(page_title="Chat With Your Docs", page_icon="📚", layout="wide")
st.title("📚 Chat With Your Docs")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "store" not in st.session_state:
    st.session_state.store = None
    st.session_state.files = []

# ------------------------------------------------------------------ sidebar: documents
with st.sidebar:
    st.header("Documents")
    uploads = st.file_uploader("Upload files", type=SUPPORTED, accept_multiple_files=True)
    use_sample = st.checkbox("Include the Nimbus Coffee sample documents", value=not uploads)
    if st.button("Build index", type="primary"):
        docs = []
        # TODO:
        #   - for each uploaded file f: docs += load_uploaded(f.name, f.getvalue())
        #   - if use_sample: for each path in sorted(KB_DIR.iterdir()):
        #         docs += load_uploaded(path.name, path.read_bytes())
        #   - if docs is empty: st.warning(...)
        #   - else: inside st.spinner(...), st.session_state.store = build_index(docs, get_embeddings())
        #           st.session_state.files = sorted set of the docs' metadata["source"]
        #           st.session_state.messages = []   (new documents, new conversation)
        st.warning("TODO: build the index — see the comments in app.py")
    if st.session_state.files:
        st.success(f"Indexed {len(st.session_state.files)} files")
        st.caption(", ".join(st.session_state.files))

# ------------------------------------------------------------------ chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if st.session_state.store is None:
    st.info("Add documents in the sidebar and click **Build index** to start.")
elif question := st.chat_input("Ask about your documents"):
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            result = answer(get_chat_model(temperature=0), st.session_state.store,
                            st.session_state.messages, question)
        st.markdown(result["answer"])
        # TODO: inside `with st.expander("Sources"):`
        #   - if result["standalone"] differs from the question, st.caption it
        #   - for each doc: st.markdown its number, source (and page if present), st.text the first 400 chars
    st.session_state.messages += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": result["answer"]},
    ]
