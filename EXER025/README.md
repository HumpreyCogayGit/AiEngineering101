# EXER025 — Chat With Your Docs

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec025.html](../Lecture/lectures/lec025.html)

## Goal

Ship a complete RAG product: a Streamlit app where users upload their own
files, ask follow-up questions in a conversation, and see the sources behind
every answer.

## Tasks

1. `starter/docs_logic.py` — `load_uploaded`, `build_index` (in-memory, per session),
   `condense_question` (rewrite follow-ups), `answer`
2. `starter/app.py` — build the index from uploads, show sources in an expander

## Run it

```bash
uv run streamlit run EXER025/starter/app.py
uv run python EXER025/check.py
```

## Success criteria

- [ ] Uploading a PDF or Markdown file and clicking "Build index" works
- [ ] Follow-ups work: "Tell me about the cold brew bottle" → "How much is it?"
- [ ] Every answer has a Sources expander with file names (and PDF page numbers)
- [ ] Two browser tabs do not see each other's documents
- [ ] All 7 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Let the user remove one uploaded file from the index. *Done when:* after Remove, the file is gone from the list and no answer cites it; the other files are not re-embedded.
2. **Connect (EXER024).** Add thumbs up/down under each answer and write the feedback to a file. *Done when:* each rating adds one line to `stretch/output/feedback.jsonl` with the question, the sources and the answer.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run streamlit run EXER025/stretch/goal1_remove_file_app.py
uv run streamlit run EXER025/stretch/goal2_feedback_app.py
```

Also in [stretch/](stretch/): `remove_file.py`.
