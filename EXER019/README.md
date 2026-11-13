# EXER019 — Embeddings and Similarity

**Module 4 · RAG** · Lecture: [Lecture/lectures/lec019.html](../Lecture/lectures/lec019.html)

## Goal

Understand embeddings, the foundation of RAG: text in, vector out, and
"similar meaning" becomes "small angle between vectors".

## Before you start

You need an **embedding model** on your provider:

- **Azure Foundry**: deploy one (recommended `text-embedding-3-small`) and set
  `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` in `.env`.
- **Ollama**: `ollama pull nomic-embed-text` (the default `OLLAMA_EMBEDDING_MODEL`).

Vectors from different embedding models have different sizes and cannot be compared.

## Tasks

Complete the TODOs in `starter/embeddings.py`:

1. `embed_texts` — batch-embed texts with `client.embeddings.create`
2. `cosine_similarity` — with numpy
3. `search` — score and rank a small corpus

## Run it

```bash
uv run python EXER019/starter/embeddings.py
uv run python EXER019/check.py
```

## Success criteria

- [ ] "How do I get my money back?" finds the refund sentence, though no words match
- [ ] "When can I take a holiday from work?" finds the vacation sentence
- [ ] You can state the dimension of your embedding vectors
- [ ] All 5 checks pass
