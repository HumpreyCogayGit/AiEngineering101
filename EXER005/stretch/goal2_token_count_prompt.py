"""EXER005 stretch goal 2 — show the running token count in the prompt (EXER004).

    uv run python EXER005/stretch/goal2_token_count_prompt.py           # interactive
    uv run python EXER005/stretch/goal2_token_count_prompt.py --demo    # a scripted run

The whole history is sent on every turn, so the number in the prompt only
goes up. It is counted locally with tiktoken (EXER004): an estimate, free,
and available BEFORE the request is sent.
"""

from __future__ import annotations

import sys

import tiktoken

from aicourse.llm import get_llm_client
from aicourse.stretch import solution_module

base = solution_module(__file__, "chatbot.py")
ENCODING = tiktoken.get_encoding("o200k_base")


def conversation_tokens(conversation) -> int:
    """Estimated tokens of everything the next request will carry."""
    # About 4 tokens per message for the role and the separators around it.
    return sum(len(ENCODING.encode(m["content"])) + 4 for m in conversation.messages)


def prompt_label(conversation) -> str:
    return f"You [{conversation_tokens(conversation)} tokens so far]: "


def demo() -> None:
    client = get_llm_client()
    convo = base.Conversation()
    for text in ("Hi, I'm Ada.", "Tell me one fact about coffee.", "And one about tea."):
        print(f"{prompt_label(convo)}{text}")
        print("Bot:", base.chat_turn(client, convo, text))
    print(f"\nThe next request already carries {conversation_tokens(convo)} tokens of history.")


def main() -> None:
    if "--demo" in sys.argv:
        return demo()
    client = get_llm_client()
    convo = base.Conversation()
    print("Chatbot ready. Commands: /reset  /exit")
    while True:
        try:
            text = input(f"\n{prompt_label(convo)}").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/exit":
            break
        if text == "/reset":
            convo.reset()
        elif text:
            print("Bot:", base.chat_turn(client, convo, text))


if __name__ == "__main__":
    main()
