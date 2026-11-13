"""EXER015 — Streamlit Chat App (reference solution).

    uv run streamlit run EXER015/solution/app.py

Streamlit re-runs this whole script from top to bottom on EVERY interaction.
Anything that must survive a re-run lives in st.session_state.
"""

import streamlit as st

from aicourse.llm import get_chat_model
from chat_logic import stream_answer

st.set_page_config(page_title="Course Chat", page_icon="💬")
st.title("💬 Course Chat")

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("Settings")
    system_prompt = st.text_area("System prompt", "You are a helpful, concise assistant.")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()


@st.cache_resource
def load_llm(temp: float):
    """Created once per temperature value, not on every re-run."""
    return get_chat_model(temperature=temp)


# ------------------------------------------------------------------ state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Re-draw the conversation so far (the script just re-ran from the top).
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ------------------------------------------------------------------ input
if prompt := st.chat_input("Ask me anything"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(
                stream_answer(load_llm(temperature), st.session_state.messages, system_prompt)
            )
        except Exception as exc:  # show the problem instead of a stack trace
            st.error(f"The model call failed: {exc}")
            answer = None
    if answer:
        st.session_state.messages.append({"role": "assistant", "content": answer})
