"""EXER015 stretch goal 2 — token usage per message in the sidebar (EXER004).

    uv run streamlit run EXER015/stretch/goal2_usage_sidebar_app.py

A streamed answer reports its usage in the last chunk, and only when asked
(`stream_usage=True`). The generator below passes the text on to
st.write_stream and keeps the usage it sees on the way. Usage is stored with
each assistant message, so the sidebar can show how the INPUT grows turn by
turn: the whole history is resent every time (EXER005).
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
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()
    usage_box = st.container()  # filled at the end of the script, when this turn's usage is known


@st.cache_resource
def load_llm():
    return get_chat_model(stream_usage=True)  # ask for the usage chunk


def stream_and_measure(llm, history: list[dict], system: str, usage: dict):
    """Yield text for the page; record token counts into `usage` as they arrive."""
    for chunk in llm.stream(logic.to_langchain_messages(history, system)):
        if chunk.usage_metadata:
            usage["input"] = usage.get("input", 0) + chunk.usage_metadata["input_tokens"]
            usage["output"] = usage.get("output", 0) + chunk.usage_metadata["output_tokens"]
        if chunk.text:
            yield chunk.text


if "messages" not in st.session_state:
    st.session_state.messages = []
history = st.session_state.messages

for message in history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything"):
    history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    usage: dict = {}
    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(stream_and_measure(load_llm(), history, system_prompt, usage))
        except Exception as exc:
            st.error(f"The model call failed: {exc}")
            answer = None
    if answer:
        history.append({"role": "assistant", "content": answer, "usage": usage})

with usage_box:
    st.subheader("Token usage")
    answers = [m for m in history if m["role"] == "assistant"]
    rows = [{"turn": i, "input": m.get("usage", {}).get("input", 0),
             "output": m.get("usage", {}).get("output", 0)} for i, m in enumerate(answers, 1)]
    if rows:
        st.dataframe(rows, hide_index=True)
        st.metric("Total tokens", sum(r["input"] + r["output"] for r in rows))
        st.caption("Input grows every turn: the whole history is sent again.")
    else:
        st.caption("Send a message to see its token usage.")
