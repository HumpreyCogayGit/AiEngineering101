# EXER020 — Loading and Chunking

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec020.html](../Lecture/lectures/lec020.html)

## Goal

Build the ingestion half of a RAG pipeline: load Markdown, HTML and PDF files
into clean `Document`s with useful metadata, and split them into chunks.

## The data

[data/knowledge_base/](../data/knowledge_base/) holds the documents of the
fictional **Nimbus Coffee Co.**: policies, products, a FAQ, a careers web page
and an employee handbook PDF. All RAG exercises use it.

## Tasks

Complete the TODOs in `starter/ingest.py`:

1. `load_text`, `load_html` (clean out scripts and navigation), `load_pdf` (one Document per page)
2. `load_directory`: pick the loader by file extension
3. `chunk_documents`: `RecursiveCharacterTextSplitter` plus a `chunk_id`

## Run it

```bash
uv run python EXER020/starter/ingest.py
uv run python EXER020/check.py
```

## Success criteria

- [ ] 9 documents are loaded from 8 files
- [ ] The HTML text contains no navigation, script or footer text
- [ ] PDF chunks keep their page number
- [ ] You can explain the trade-off between chunk sizes 200, 600 and 1500
- [ ] All 7 checks pass (offline, no API key needed)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a Markdown-header-aware splitter and compare its chunks with the recursive splitter's. *Done when:* every Markdown chunk holds exactly one section, and the statistics of both splitters are printed.
2. **Connect (EXER022).** Record the heading path of each chunk (`Brewing Guide > French press`) in its metadata. *Done when:* every Markdown chunk has a `heading_path`, and it appears next to the source in a formatted prompt.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER020/stretch/goal1_markdown_splitter.py
uv run python EXER020/stretch/goal2_heading_path.py
```
