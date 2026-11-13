"""EXER025 — Chat With Your Docs (reference solution).

    uv run streamlit run EXER025/solution/app.py
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
        for f in uploads or []:
            docs += load_uploaded(f.name, f.getvalue())
        if use_sample:
            for path in sorted(KB_DIR.iterdir()):
                docs += load_uploaded(path.name, path.read_bytes())
        if not docs:
            st.warning("Upload a file or tick the sample documents first.")
        else:
            with st.spinner(f"Embedding {len(docs)} documents..."):
                st.session_state.store = build_index(docs, get_embeddings())
            st.session_state.files = sorted({d.metadata["source"] for d in docs})
            st.session_state.messages = []
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
        with st.expander("Sources"):
            if result["standalone"] != question:
                st.caption(f"Searched for: *{result['standalone']}*")
            for i, d in enumerate(result["docs"], 1):
                page = f", page {d.metadata['page']}" if "page" in d.metadata else ""
                st.markdown(f"**[{i}] {d.metadata.get('source')}{page}**")
                st.text(d.page_content[:400])
    st.session_state.messages += [
        {"role": "user", "content": question},
        {"role": "assistant", "content": result["answer"]},
    ]
