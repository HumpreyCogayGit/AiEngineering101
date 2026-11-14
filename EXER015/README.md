# EXER015 — Streamlit Chat App

**Module 2 · LangChain** · Lecture: [Lecture/lectures/lec015.html](../Lecture/lectures/lec015.html)

## Goal

Put your chatbot in the browser: Streamlit's execution model, session state,
chat elements and streaming to the UI.

## Tasks

1. `starter/chat_logic.py`: `to_langchain_messages`, `stream_answer`
2. `starter/app.py`: session state, re-drawing history, handling the prompt, clear button

## Run it

```bash
uv run streamlit run EXER015/starter/app.py
uv run python EXER015/check.py
```

The app opens at http://localhost:8501.

## Success criteria

- [ ] Answers stream into the assistant bubble
- [ ] The conversation stays visible after each message (session state works)
- [ ] Changing the system prompt in the sidebar changes the bot's behaviour
- [ ] "Clear conversation" empties the chat
- [ ] All 5 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a Regenerate button that replaces the last answer. *Done when:* clicking it removes the last assistant message and a new answer to the same question appears.
2. **Connect (EXER004).** Show token usage per message in the sidebar. *Done when:* the sidebar lists input and output tokens per turn, and the input grows from turn to turn.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run streamlit run EXER015/stretch/goal1_regenerate_app.py
uv run streamlit run EXER015/stretch/goal2_usage_sidebar_app.py
```
