# EXER006 — Message Content Blocks

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec006.html](../Lecture/lectures/lec006.html)

## Goal

Learn that message `content` can be a **list of typed blocks** (text, image),
send an image to the model, and keep long conversations inside the context
window by trimming history.

## Tasks

Complete the TODOs in `starter/content_blocks.py`:

1. `text_block`, `image_block_from_url`, `image_block_from_file` (base64 data URL)
2. `build_multimodal_message` — one user message with a text block and image blocks
3. `describe_image` — ask a question about [images/shapes.png](images/shapes.png)
4. `trim_history` — keep the system prompt and the newest messages that fit a token budget

## Run it

```bash
uv run python EXER006/starter/content_blocks.py
uv run python EXER006/check.py
```

## Success criteria

- [ ] The model correctly describes the red circle, blue square and green triangle
- [ ] A 41-message history is trimmed to fit 400 tokens, keeping the newest turns
- [ ] All 7 checks pass

> Your chat deployment must support image input (gpt-4.1-mini, gpt-4o-mini, gpt-4o … do).
