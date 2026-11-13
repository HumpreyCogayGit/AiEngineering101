"""Nimbus Helpdesk — web UI.

    uv run streamlit run EXER037/solution/app.py
"""

import asyncio
import uuid

import streamlit as st

from assistant import Assistant

st.set_page_config(page_title="Nimbus Helpdesk", page_icon="☕")
st.title("☕ Nimbus Helpdesk")
st.caption("Ask about products, orders, shipping, refunds, stores or jobs. I can also take notes for you.")


def new_session() -> None:
    st.session_state.thread_id = uuid.uuid4().hex
    st.session_state.messages = []


if "thread_id" not in st.session_state:
    new_session()
if "assistant" not in st.session_state:
    st.session_state.assistant = Assistant()

with st.sidebar:
    st.header("Session")
    st.caption(f"Thread `{st.session_state.thread_id[:8]}`")
    show_details = st.toggle("Show tools and tokens", value=True)
    if st.button("New conversation"):
        new_session()
        st.rerun()

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("details") and show_details:
            st.caption(m["details"])

if question := st.chat_input("How can I help?"):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                reply = asyncio.run(st.session_state.assistant.ask(question, st.session_state.thread_id))
                answer = reply.answer
                details = (f"🔧 {', '.join(reply.tools_used) or 'no tools'} · {reply.tokens} tokens"
                           + (f" · ⛔ blocked: {', '.join(reply.reasons)}" if reply.blocked else ""))
            except Exception as exc:
                answer, details = f"Something went wrong: {exc}", ""
        st.markdown(answer)
        if details and show_details:
            st.caption(details)
    st.session_state.messages.append({"role": "assistant", "content": answer, "details": details})
