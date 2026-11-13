"""EXER028 — Memory and Persistence.

Two kinds of memory:
  SHORT-TERM  = the conversation of ONE thread. A checkpointer saves the graph
                state after every step, keyed by thread_id. (InMemorySaver for
                tests, SqliteSaver to survive restarts.)
  LONG-TERM   = facts about a USER that last across all their threads. Kept in
                a Store, under a namespace such as ("memories", user_id).

    uv run python EXER028/starter/memory_bot.py
    uv run python EXER028/check.py
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, trim_messages
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from pydantic import BaseModel, Field

from aicourse.llm import get_chat_model

MAX_HISTORY = 20  # messages sent to the model (the checkpoint still keeps everything)
DB_PATH = Path(__file__).resolve().parent / "output" / "memory.sqlite"


class MemoryUpdate(BaseModel):
    facts: list[str] = Field(
        description="New durable facts about the user (name, preferences, allergies, goals). "
                    "Empty if the message contains none."
    )


def namespace(user_id: str) -> tuple[str, str]:
    return ("memories", user_id)


def recall(store: BaseStore, user_id: str) -> list[str]:
    """All facts stored for this user: [item.value["fact"] for item in store.search(namespace(user_id))]"""
    # TODO
    raise NotImplementedError("recall")


def build_chatbot(llm: BaseChatModel, checkpointer=None, store: BaseStore | None = None):
    extractor = llm.with_structured_output(MemoryUpdate)

    def chat(state: MessagesState, config: RunnableConfig, runtime: Runtime) -> dict:
        """LangGraph passes `config` (with your thread_id / user_id) and `runtime` (with .store).

        1. user_id = config["configurable"].get("user_id", "anonymous")
        2. facts = recall(runtime.store, user_id); add them to the system prompt if any
        3. recent = trim_messages(state["messages"], strategy="last", token_counter=len,
                                  max_tokens=MAX_HISTORY, start_on="human")
           (token_counter=len counts MESSAGES, so this keeps the last MAX_HISTORY messages)
        4. return {"messages": [llm.invoke([SystemMessage(system)] + recent)]}
        """
        # TODO
        raise NotImplementedError("chat node")

    def save_memories(state: MessagesState, config: RunnableConfig, runtime: Runtime) -> dict:
        """Extract durable facts from the LAST human message and store the new ones.

        - last_user = the last message whose .type == "human"
        - update = extractor.invoke("Extract durable facts about the user from this message, if any:\n" + content)
        - for each fact not already known: runtime.store.put(namespace(user_id), str(uuid.uuid4()), {"fact": fact})
        - return {}   (this node changes no state)
        """
        # TODO
        raise NotImplementedError("save_memories node")

    builder = StateGraph(MessagesState)
    builder.add_node("chat", chat)
    builder.add_node("save_memories", save_memories)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", "save_memories")
    builder.add_edge("save_memories", END)
    # TODO: compile WITH memory:
    #   builder.compile(checkpointer=checkpointer or InMemorySaver(),
    #                   store=store if store is not None else InMemoryStore())
    return builder.compile()


def sqlite_checkpointer(path: str | Path = DB_PATH) -> SqliteSaver:
    """A checkpointer that survives restarts.
    Create the parent folder, then SqliteSaver(sqlite3.connect(str(path), check_same_thread=False))"""
    # TODO
    raise NotImplementedError("sqlite_checkpointer")


def config_for(thread_id: str, user_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id, "user_id": user_id}}


def send(graph, text: str, thread_id: str, user_id: str = "user-1") -> str:
    result = graph.invoke({"messages": [("user", text)]}, config_for(thread_id, user_id))
    return result["messages"][-1].text


def history(graph, thread_id: str, user_id: str = "user-1") -> list:
    return graph.get_state(config_for(thread_id, user_id)).values.get("messages", [])


def main() -> None:
    store = InMemoryStore()
    graph = build_chatbot(get_chat_model(temperature=0), checkpointer=sqlite_checkpointer(), store=store)

    print("Thread A:", send(graph, "Hi! I'm Bea and I'm allergic to dairy.", "thread-a"))
    print("Thread A:", send(graph, "What's my name?", "thread-a"))
    print("Thread B (same user, new conversation):", send(graph, "Suggest a drink for me.", "thread-b"))
    print("Thread C (other user):", send(graph, "What's my name?", "thread-c", user_id="user-2"))
    print("\nLong-term memories of user-1:", recall(store, "user-1"))
    print(f"Thread A has {len(history(graph, 'thread-a'))} messages saved in {DB_PATH}")
    print("Run again: thread A's conversation is restored from SQLite.")


if __name__ == "__main__":
    main()
