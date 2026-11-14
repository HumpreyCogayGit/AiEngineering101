"""EXER005 stretch goal 1 — `/save` and `/load` the conversation.

    uv run python EXER005/stretch/goal1_save_load.py            # interactive
    uv run python EXER005/stretch/goal1_save_load.py --demo     # a scripted run, no typing

"Memory" is the message list, so saving a conversation is writing that list
to a file, and loading it is reading the list back. Nothing about the model
has to be saved: it never had any state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from aicourse.llm import get_llm_client
from aicourse.stretch import solution_module

base = solution_module(__file__, "chatbot.py")

SAVE_DIR = Path(__file__).resolve().parent / "output"


def save(conversation, name: str) -> Path:
    SAVE_DIR.mkdir(exist_ok=True)
    path = SAVE_DIR / f"{Path(name).name}.json"  # .name: never write outside SAVE_DIR
    path.write_text(json.dumps(conversation.messages, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load(conversation, name: str) -> int:
    """Replace the conversation with a saved one. Returns the number of messages."""
    messages = json.loads((SAVE_DIR / f"{Path(name).name}.json").read_text(encoding="utf-8"))
    if not messages or messages[0].get("role") != "system":
        raise ValueError("not a saved conversation: the first message must be the system prompt")
    conversation.messages = messages
    conversation.system_prompt = messages[0]["content"]  # so /reset keeps the loaded prompt
    return len(messages)


def handle_command(conversation, text: str) -> str | None:
    """Run /save or /load. Returns the line to print, or None if `text` is not one of them."""
    command, _, name = text.partition(" ")
    name = name.strip() or "conversation"
    if command == "/save":
        return f"(saved {len(conversation.messages)} messages to {save(conversation, name)})"
    if command == "/load":
        try:
            return f"(loaded {load(conversation, name)} messages)"
        except (OSError, ValueError) as exc:
            return f"(cannot load '{name}': {exc})"
    return None


def demo() -> None:
    client = get_llm_client()
    first = base.Conversation()
    print("Bot:", base.chat_turn(client, first, "Hi, my name is Ada and I roast coffee."))
    print(handle_command(first, "/save ada"))

    second = base.Conversation()  # a brand-new conversation: it knows nothing
    print(handle_command(second, "/load ada"))
    print("Bot:", base.chat_turn(client, second, "What is my name, and what do I do?"))


def main() -> None:
    if "--demo" in sys.argv:
        return demo()
    client = get_llm_client()
    convo = base.Conversation()
    print("Chatbot ready. Commands: /save [name]  /load [name]  /reset  /exit")
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text == "/exit":
            break
        if text == "/reset":
            convo.reset()
            print("(conversation cleared)")
        elif (reply := handle_command(convo, text)) is not None:
            print(reply)
        elif text:
            print("Bot:", base.chat_turn(client, convo, text))


if __name__ == "__main__":
    main()
