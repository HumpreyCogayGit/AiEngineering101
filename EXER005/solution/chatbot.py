"""EXER005 — Messages and Roles (reference solution).

A terminal chatbot that remembers the conversation. The model itself is
STATELESS: it remembers nothing between calls. "Memory" is just us sending
the whole message list every time.
"""

from __future__ import annotations

from aicourse.llm import get_openai_client
from aicourse.settings import get_settings

DEFAULT_SYSTEM = "You are a friendly, concise assistant. Keep answers under 80 words."


class Conversation:
    def __init__(self, system_prompt: str = DEFAULT_SYSTEM) -> None:
        self.system_prompt = system_prompt
        self.messages: list[dict] = [{"role": "system", "content": system_prompt}]

    def add_user(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})

    def add_assistant(self, text: str) -> None:
        self.messages.append({"role": "assistant", "content": text})

    def reset(self) -> None:
        """Forget everything except the system prompt."""
        self.messages = [{"role": "system", "content": self.system_prompt}]

    def to_api(self) -> list[dict]:
        """A copy of the messages, ready to send."""
        return [dict(m) for m in self.messages]


def chat_turn(client, conversation: Conversation, user_text: str) -> str:
    """One round trip: add the user message, call the model, store and return the reply."""
    conversation.add_user(user_text)
    response = client.chat.completions.create(
        model=get_settings().chat_deployment,
        messages=conversation.to_api(),
    )
    reply = response.choices[0].message.content or ""
    conversation.add_assistant(reply)
    return reply


def main() -> None:
    client = get_openai_client()
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
