"""EXER012 stretch goal 2 — run the chatbot offline with the fake chat model.

    uv run python EXER012/stretch/goal2_offline_chatbot.py      # no network, no key, no cost

LCConversation only needs "something with invoke()". Because every LangChain
chat model has the same interface, a scripted fake can stand in for the real
one. This is how the course's checks test your code for free, and how you
test yours: the fake returns what you tell it and records what it was sent.
"""

from __future__ import annotations

from aicourse.fakes import fake_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "lc_chat.py")


def main() -> None:
    fake = fake_chat_model("Nice to meet you, Ada.", "Your name is Ada.")
    convo = base.LCConversation(fake, "You are a helpful assistant.")

    print("Bot:", convo.send("Hi, I'm Ada."))
    print("Bot:", convo.send("What's my name?"))

    print("\nWhat the 'model' received on the second turn:")
    for message in fake.received[-1]:
        print(f"  {type(message).__name__:<14} {message.content}")

    # The same assertions a check script would make:
    assert len(fake.received) == 2, "one model call per turn"
    assert [type(m).__name__ for m in fake.received[-1]] == [
        "SystemMessage", "HumanMessage", "AIMessage", "HumanMessage"
    ], "the whole history is resent, in order"
    print("\nBoth assertions hold: the conversation logic is correct, proven without a model.")


if __name__ == "__main__":
    main()
