# EXER005 — Messages and Roles

**Module 1 · Talking to an LLM** · Lecture: [Lecture/lectures/lec005.html](../Lecture/lectures/lec005.html)

## Goal

Understand the `system`, `user` and `assistant` roles, and learn that the model
is **stateless**: a chatbot "remembers" only because you resend the whole
conversation each turn.

## Tasks

Complete the TODOs in `starter/chatbot.py`:

1. `Conversation` — store the message list, starting with the system prompt
2. `add_user`, `add_assistant`, `reset`
3. `chat_turn` — send the full history, store the reply, return it

## Run it

```bash
uv run python EXER005/starter/chatbot.py
uv run python EXER005/check.py
```

Try: tell the bot your name, then ask for it. Then type `/reset` and ask again.

## Success criteria

- [ ] The bot remembers facts from earlier turns
- [ ] After `/reset` it has forgotten them
- [ ] `/history` shows the system, user and assistant messages in order
- [ ] All 6 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add `/save` and `/load` commands that write the conversation to a JSON file and read it back. *Done when:* a brand-new conversation that loads the file can answer a question about the saved one.
2. **Connect (EXER004).** Show the running token count of the conversation in the input prompt. *Done when:* the number in `You [N tokens so far]:` grows on every turn.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER005/stretch/goal1_save_load.py --demo
uv run python EXER005/stretch/goal2_token_count_prompt.py --demo
```
