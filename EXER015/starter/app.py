"""EXER015 — Streamlit Chat App.

    uv run streamlit run EXER015/starter/app.py

Streamlit re-runs this whole script from top to bottom on EVERY interaction.
Anything that must survive a re-run lives in st.session_state.

Complete the TODOs in chat_logic.py first, then the TODOs below.
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
    # TODO: add a "Clear conversation" button that empties st.session_state.messages
    #       and calls st.rerun()


@st.cache_resource
def load_llm(temp: float):
    """Created once per temperature value, not on every re-run."""
    return get_chat_model(temperature=temp)


# ------------------------------------------------------------------ state
# TODO: if "messages" is not in st.session_state, set it to an empty list


# TODO: re-draw the conversation so far. For each message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])


# ------------------------------------------------------------------ input
if prompt := st.chat_input("Ask me anything"):
    # TODO:
    #   1. append {"role": "user", "content": prompt} to st.session_state.messages
    #   2. show it inside `with st.chat_message("user"):`
    #   3. inside `with st.chat_message("assistant"):`
    #        answer = st.write_stream(stream_answer(load_llm(temperature), st.session_state.messages, system_prompt))
    #      (wrap it in try/except and show st.error(...) if the call fails)
    #   4. append the assistant answer to st.session_state.messages
    st.warning("TODO: handle the prompt — see the comments in app.py")
