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

> Your chat model must support image input (gpt-4.1-mini, gpt-4o-mini, gpt-4o … do; on Ollama,
> `ollama show <model>` must list the `vision` capability, as it does for gemma4:e4b).

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Send two images in one message and ask for the differences (`images/shapes_changed.png` is the second image). *Done when:* the answer names the colour change, the missing triangle and the changed label.
2. **Connect (EXER005).** Trim by summarizing the dropped turns into one message instead of deleting them. *Done when:* after trimming, the bot still knows an order number from the first turn, which plain trimming forgets.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER006/stretch/goal1_two_images.py
uv run python EXER006/stretch/goal2_summarize_dropped.py
```
