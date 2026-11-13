"""EXER031 — Multi-Agent Systems (reference solution).

The SUPERVISOR pattern: one coordinator decides which specialist works next.
Each specialist is itself an agent (a subgraph) with its own prompt and tools.

Two ways to coordinate the same two specialists:

- build_team()          SUPERVISOR: a coordinator picks the next worker each turn
- build_handoff_team()  HANDOFF: an agent passes control straight to the next one

Use multi-agent only when one agent really struggles: separate tools, separate
expertise, or a context window that gets too crowded. Every hop costs latency
and tokens.
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

    researcher = create_agent(
        llm, [search_documents], name="researcher",
        system_prompt="You are a researcher. Use search_documents to find facts that answer the "
                      "customer's request. Report the facts as short bullet points with their sources. "
                      "Do not write the customer reply.",
    )
    writer = create_agent(
        llm, [], name="writer",
        system_prompt="You write warm, concise customer replies (max 120 words) using ONLY the "
                      "researcher's facts in the conversation. Sign as 'Nimbus Support'.",
    )
    return researcher, writer


# ------------------------------------------------------- 1. supervisor
def build_team(llm: BaseChatModel, search: Callable[[str], str]):
    researcher, writer = make_workers(llm, search)
    supervisor = llm.with_structured_output(Route)

    def supervise(state: TeamState) -> dict:
        steps = state.get("steps", [])
        if len(steps) >= MAX_STEPS:
            return {"next": "FINISH", "instruction": "step limit reached"}
        route = supervisor.invoke([SystemMessage(SUPERVISOR_PROMPT)] + state["messages"])
        if route.next == "FINISH" and "writer" not in steps:
            # The prompt ASKS the supervisor to finish only after the writer. A rule that
            # must always hold is enforced in code: some models finish as soon as the
            # research looks like an answer.
            missing = "writer" if "researcher" in steps else "researcher"
            return {"next": missing, "instruction": route.instruction}
        return {"next": route.next, "instruction": route.instruction}

    def make_worker(name: str, agent):
        def run(state: TeamState) -> dict:
            task = HumanMessage(content=f"[Supervisor → {name}] {state['instruction']}")
            result = agent.invoke({"messages": state["messages"] + [task]})
            reply = AIMessage(content=result["messages"][-1].text, name=name)
            return {"messages": [reply], "steps": [name]}
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
    """The same specialists with no supervisor.

    A node returns Command(goto=..., update=...): it updates the state AND names
    the next node. The researcher hands off to the writer when it looked something
    up, and ends the run itself when there was nothing to research.
    """
    researcher, writer = make_workers(llm, search)

    def research(state: TeamState) -> Command:
        result = researcher.invoke({"messages": state["messages"]})
        used_search = any(isinstance(m, ToolMessage) for m in result["messages"])
        note = AIMessage(content=result["messages"][-1].text, name="researcher")
        return Command(
            goto="writer" if used_search else END,  # the handoff decision
            update={"messages": [note], "steps": ["researcher"]},
        )

    def write(state: TeamState) -> Command:
        result = writer.invoke({"messages": state["messages"]})
        reply = AIMessage(content=result["messages"][-1].text, name="writer")
        return Command(goto=END, update={"messages": [reply], "steps": ["writer"]})

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
