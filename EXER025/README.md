# EXER025 — Chat With Your Docs

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec025.html](../Lecture/lectures/lec025.html)

## Goal

Ship a complete RAG product: a Streamlit app where users upload their own
files, ask follow-up questions in a conversation, and see the sources behind
every answer.

## Tasks

1. `starter/docs_logic.py`: `load_uploaded`, `build_index` (in-memory, per session),
   `condense_question` (rewrite follow-ups), `answer`
2. `starter/app.py`: build the index from uploads, show sources in an expander

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

## Transfer task (end of Module 4)

Optional, and different from the stretch goals: a new problem in a new domain, with **no starter code and no `check.py`**. It shows whether you can use Module 4's ideas without scaffolding.

Answer questions about **Harbor Bikes**, a bike rental company, from the three documents in
[transfer/harbor_docs/](transfer/harbor_docs/) (Markdown and HTML), with no starter code. Measure your
pipeline with the ten golden questions in [transfer/questions.json](transfer/questions.json); two of them
cannot be answered from the documents.

- [ ] The documents are loaded, chunked and indexed in their own collection, not the Nimbus one
- [ ] Answers cite their passages, and say they don't know when the documents don't cover the question
- [ ] The script reports hit rate, MRR, correctness and refusal as four separate numbers (EXER024)
- [ ] You changed one thing (chunk size, k, or the prompt) and can say which number it moved

Reference answer, for after you have tried:

```bash
uv run python EXER025/transfer/reference_harbor_rag.py
```
