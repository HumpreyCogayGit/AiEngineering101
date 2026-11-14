"""EXER015 stretch goal 1 — a "Regenerate" button for the last answer.

    uv run streamlit run EXER015/stretch/goal1_regenerate_app.py

Regenerating means: forget the last assistant message and answer the same
question again. The button only changes session state and re-runs; the
answering code below it then finds a history that ends with a user message
and does the rest. One code path answers both a new and a regenerated turn.
"""

import streamlit as st

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

logic = solution_module(__file__, "chat_logic.py")

st.set_page_config(page_title="Course Chat", page_icon="💬")
st.title("💬 Course Chat")

with st.sidebar:
    st.header("Settings")
    system_prompt = st.text_area("System prompt", "You are a helpful, concise assistant.")
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()


@st.cache_resource
def load_llm(temp: float):
    return get_chat_model(temperature=temp)


def needs_answer(history: list[dict]) -> bool:
    """True when the last message is a question nobody has answered yet."""
    return bool(history) and history[-1]["role"] == "user"


if "messages" not in st.session_state:
    st.session_state.messages = []
history = st.session_state.messages

if prompt := st.chat_input("Ask me anything"):
    history.append({"role": "user", "content": prompt})

for message in history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if needs_answer(history):
    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(logic.stream_answer(load_llm(temperature), history, system_prompt))
        except Exception as exc:
            st.error(f"The model call failed: {exc}")
            answer = None
    if answer:
        history.append({"role": "assistant", "content": answer})

# Offer the button only when there is an answer to replace.
if history and history[-1]["role"] == "assistant":
    if st.button("↻ Regenerate"):
        history.pop()  # drop the answer; the question before it is now unanswered
        st.rerun()     # the re-run reaches needs_answer() and answers it again
