"""EXER005 — Messages and Roles.

Build a terminal chatbot that remembers the conversation. The model itself is
STATELESS: it remembers nothing between calls. "Memory" is just us sending
the whole message list every time.

From now on we use the ready-made helper `get_llm_client()` — it does
exactly what you wrote in EXER004's make_client().

    uv run python EXER005/starter/chatbot.py
    uv run python EXER005/check.py
"""

from __future__ import annotations

from aicourse.llm import get_llm_client
from aicourse.settings import get_settings

DEFAULT_SYSTEM = "You are a friendly, concise assistant. Keep answers under 80 words."


class Conversation:
    def __init__(self, system_prompt: str = DEFAULT_SYSTEM) -> None:
        self.system_prompt = system_prompt
        # TODO: start self.messages as a list holding ONE system message dict
        self.messages: list[dict] = []

    def add_user(self, text: str) -> None:
        # TODO: append {"role": "user", "content": text}
        raise NotImplementedError("Conversation.add_user")

    def add_assistant(self, text: str) -> None:
        # TODO: append an assistant message
        raise NotImplementedError("Conversation.add_assistant")

    def reset(self) -> None:
        """Forget everything except the system prompt."""
        # TODO
        raise NotImplementedError("Conversation.reset")

    def to_api(self) -> list[dict]:
        """A copy of the messages, ready to send (so callers can't modify our history)."""
        return [dict(m) for m in self.messages]


def chat_turn(client, conversation: Conversation, user_text: str) -> str:
    """One round trip.

    1. add the user message to the conversation
    2. call client.chat.completions.create(model=..., messages=conversation.to_api())
    3. take the reply text, add it to the conversation as an assistant message
    4. return the reply
    """
    # TODO
    raise NotImplementedError("chat_turn")


def main() -> None:
    client = get_llm_client()
    convo = Conversation()
    print("Chatbot ready. Commands: /history  /reset  /exit")
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text == "/exit":
            break
        if text == "/reset":
            convo.reset()
            print("(conversation cleared)")
            continue
        if text == "/history":
            for m in convo.messages:
                print(f"  [{m['role']}] {m['content'][:80]}")
            continue
        print("Bot:", chat_turn(client, convo, text))
    print("Bye!")


if __name__ == "__main__":
    main()
