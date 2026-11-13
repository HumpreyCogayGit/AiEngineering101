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

## Stretch

- Change the system prompt to "You are a pirate". How much does one line change the behaviour?
- Print the total tokens sent per turn. Watch it grow — that is why EXER006 covers trimming.
