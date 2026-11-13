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
2. `load_directory` — pick the loader by file extension
3. `chunk_documents` — `RecursiveCharacterTextSplitter` plus a `chunk_id`

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
