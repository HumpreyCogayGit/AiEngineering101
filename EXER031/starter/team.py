"""EXER031 — Multi-Agent Systems.

The SUPERVISOR pattern: one coordinator decides which specialist works next.
Each specialist is itself an agent (a subgraph) with its own prompt and tools.

Use multi-agent only when one agent really struggles: separate tools, separate
expertise, or a context window that gets too crowded. Every hop costs latency
and tokens.

    uv run python EXER031/starter/team.py
    uv run python EXER031/check.py
"""

from __future__ import annotations

import operator
from typing import Annotated, Callable, Literal

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

from aicourse.llm import get_chat_model
from aicourse.rag import format_docs, get_vector_store

MAX_STEPS = 6
WORKERS = ("researcher", "writer")


class Route(BaseModel):
    next: Literal["researcher", "writer", "FINISH"] = Field(
        description="researcher = find facts in company documents; writer = draft the final customer "
                    "reply from the research; FINISH = the writer has produced the final reply."
    )
    instruction: str = Field(description="What the chosen worker should do next")


class TeamState(MessagesState):
    next: str
    instruction: str
    steps: Annotated[list[str], operator.add]


SUPERVISOR_PROMPT = (
    "You are the supervisor of a customer-support team at Nimbus Coffee Co.\n"
    "Workers: researcher (searches company documents), writer (writes the customer reply).\n"
    "Typical flow: researcher first, then writer, then FINISH. Never send the writer before "
    "there is research. Choose FINISH only after the writer has replied."
)


def make_workers(llm: BaseChatModel, search: Callable[[str], str]):
    """The two specialists. Each one is a complete agent (a subgraph)."""
    @tool
    def search_documents(query: str) -> str:
        """Search Nimbus Coffee company documents (policies, products, shipping, stores, jobs)."""
        return search(query)

    # TODO: researcher = create_agent(llm, [search_documents], name="researcher", system_prompt=...)
    #       Its prompt: find facts with search_documents, report bullet points with sources,
    #       do NOT write the customer reply.
    researcher = None

    # TODO: writer = create_agent(llm, [], name="writer", system_prompt=...)
    #       Its prompt: warm, concise reply (max 120 words) using ONLY the researcher's facts,
    #       signed 'Nimbus Support'.
    writer = None

    if researcher is None or writer is None:
        raise NotImplementedError("make_workers")
    return researcher, writer


# ------------------------------------------------------- 1. supervisor
def build_team(llm: BaseChatModel, search: Callable[[str], str]):
    researcher, writer = make_workers(llm, search)
    supervisor = llm.with_structured_output(Route)

    def supervise(state: TeamState) -> dict:
        """Decide who works next.

        - if len(state.get("steps", [])) >= MAX_STEPS: return {"next": "FINISH", "instruction": "step limit reached"}
        - route = supervisor.invoke([SystemMessage(SUPERVISOR_PROMPT)] + state["messages"])
        - GUARD: if route.next == "FINISH" but "writer" is not in steps yet, do not finish.
          Send the missing worker instead ("writer" if "researcher" is in steps, else
          "researcher"), keeping route.instruction. The prompt asks for this order, but a
          rule that must always hold belongs in code.
        - return {"next": route.next, "instruction": route.instruction}
        """
        # TODO
        raise NotImplementedError("supervise")

    def make_worker(name: str, agent):
        def run(state: TeamState) -> dict:
            """Run the sub-agent and report back.

            task = HumanMessage(f"[Supervisor → {name}] {state['instruction']}")
            result = agent.invoke({"messages": state["messages"] + [task]})
            Return {"messages": [AIMessage(content=<last message's .text>, name=name)], "steps": [name]}
            (Only the worker's FINAL message goes back into the shared conversation.)
            """
            # TODO
            raise NotImplementedError(f"{name} worker")
        return run

    def route(state: TeamState) -> str:
        return END if state["next"] == "FINISH" else state["next"]

    builder = StateGraph(TeamState)
    builder.add_node("supervisor", supervise)
    builder.add_node("researcher", make_worker("researcher", researcher))
    builder.add_node("writer", make_worker("writer", writer))
    builder.add_edge(START, "supervisor")
    builder.add_conditional_edges("supervisor", route, [*WORKERS, END])
    for worker in WORKERS:
        builder.add_edge(worker, "supervisor")  # workers always report back
    return builder.compile()


# ---------------------------------------------------------- 2. handoff
def build_handoff_team(llm: BaseChatModel, search: Callable[[str], str]):
    """The same specialists with no supervisor: agents pass control directly.

    A node may return Command(goto=<next node>, update=<state update>) instead of
    a plain dict: it updates the state AND chooses where to go next.
    """
    researcher, writer = make_workers(llm, search)

    def research(state: TeamState) -> Command:
        """Run the researcher, then hand off.

        result = researcher.invoke({"messages": state["messages"]})
        used_search = any message in result["messages"] is a ToolMessage
        note = AIMessage(content=<last message's .text>, name="researcher")
        return Command(goto="writer" if used_search else END,
                       update={"messages": [note], "steps": ["researcher"]})
        """
        # TODO
        raise NotImplementedError("research (handoff)")

    def write(state: TeamState) -> Command:
        """Run the writer, then end: Command(goto=END, update={"messages": [reply], "steps": ["writer"]})"""
        # TODO
        raise NotImplementedError("write (handoff)")

    builder = StateGraph(TeamState)
    # `destinations` only documents where a Command may go, so the graph can be drawn.
    builder.add_node("researcher", research, destinations=("writer", END))
    builder.add_node("writer", write, destinations=(END,))
    builder.add_edge(START, "researcher")
    return builder.compile()


def kb_search(query: str) -> str:
    return format_docs(get_vector_store().similarity_search(query, k=3))


def final_reply(result: dict) -> str:
    writer_msgs = [m for m in result["messages"] if getattr(m, "name", None) == "writer"]
    return writer_msgs[-1].text if writer_msgs else result["messages"][-1].text


def main() -> None:
    team = build_team(get_chat_model(temperature=0), kb_search)
    request = ("Customer email: 'Hi! My grinder arrived broken yesterday, and I also wonder if I can "
               "bring my dog when I pick up a replacement at your café?'")
    for update in team.stream({"messages": [("user", request)]}, stream_mode="updates"):
        for node, change in update.items():
            if node == "supervisor":
                print(f"\n[supervisor] next={change['next']}: {change['instruction']}")
            else:
                print(f"[{node}] {change['messages'][-1].text[:300]}")

    print("\n=== The same request with handoffs (no supervisor) ===")
    result = build_handoff_team(get_chat_model(temperature=0), kb_search).invoke({"messages": [("user", request)]})
    print("steps:", " -> ".join(result["steps"]))
    print(final_reply(result))


if __name__ == "__main__":
    main()
