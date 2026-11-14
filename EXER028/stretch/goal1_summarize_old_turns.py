"""EXER028 stretch goal 1 — summarize old turns when the thread grows long.

    uv run python EXER028/stretch/goal1_summarize_old_turns.py

Trimming (the exercise) hides old messages from the model but keeps them in
the checkpoint forever, and what is hidden is forgotten. Here a `summarize`
node runs after each reply: once the thread is longer than KEEP_LAST + a
margin, it condenses the oldest messages into `state["summary"]` and DELETES
them from the state with RemoveMessage. The thread stays short, and the
summary is put in the system prompt on every turn.

    START -> chat -> summarize? -> END
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from aicourse.llm import get_chat_model

SUMMARIZE_ABOVE = 6   # messages in the thread before we condense
KEEP_LAST = 2         # the newest messages are kept word for word


class State(MessagesState):
    summary: str


def build_chatbot(llm, checkpointer=None):
    def chat(state: State) -> dict:
        system = "You are the friendly Nimbus Coffee assistant. Keep answers to two sentences."
        if state.get("summary"):
            system += f"\nSummary of the conversation so far:\n{state['summary']}"
        return {"messages": [llm.invoke([SystemMessage(content=system)] + state["messages"])]}

    def needs_summary(state: State) -> str:
        return "summarize" if len(state["messages"]) > SUMMARIZE_ABOVE else END

    def summarize(state: State) -> dict:
        old = state["messages"][:-KEEP_LAST]
        transcript = "\n".join(f"{m.type}: {m.text}" for m in old)
        previous = f"Existing summary:\n{state['summary']}\n\n" if state.get("summary") else ""
        summary = llm.invoke([HumanMessage(content=(
            f"{previous}New messages:\n{transcript}\n\n"
            "Write an updated summary in at most 80 words. Keep every name, number, preference and decision."
        ))]).text
        # RemoveMessage tells the messages reducer to delete by id instead of appending.
        return {"summary": summary, "messages": [RemoveMessage(id=m.id) for m in old]}

    builder = StateGraph(State)
    builder.add_node("chat", chat)
    builder.add_node("summarize", summarize)
    builder.add_edge(START, "chat")
    builder.add_conditional_edges("chat", needs_summary, ["summarize", END])
    builder.add_edge("summarize", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


def main() -> None:
    graph = build_chatbot(get_chat_model(temperature=0))
    config = {"configurable": {"thread_id": "long-thread"}}
    turns = [
        "Hi, I'm Bea. I'm allergic to dairy and my order number is 4471.",
        "What is a flat white?",
        "And a cortado?",
        "Which of the two is stronger?",
        "Given what you know about me, which one can I order, and how?",
        "Remind me: what is my order number?",
    ]
    for text in turns:
        result = graph.invoke({"messages": [("user", text)]}, config)
        print(f"You: {text}\nBot: {result['messages'][-1].text[:170]}")
        print(f"     [{len(result['messages'])} messages in the thread, "
              f"summary: {'yes' if result.get('summary') else 'no'}]")
    print("\nSummary kept in the state:\n ", graph.get_state(config).values["summary"])


if __name__ == "__main__":
    main()
