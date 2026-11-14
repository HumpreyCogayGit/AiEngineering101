"""EXER027 stretch goal 1 — a per-run tool budget.

    uv run python EXER027/stretch/goal1_tool_budget.py

The recursion limit is an emergency brake: it stops the run with an error.
A tool budget is a polite limit: after N tool calls the agent must answer
with what it has. Both are enforced in code, because "use at most 3 tools"
in a prompt is a request, not a guarantee.

    agent --tool calls, budget left--> tools --> agent
      |
      +--tool calls, budget used up--> wrap_up --> END
      +--no tool calls-----------------------------> END

wrap_up answers every pending tool call with "not executed" (a tool call
must never be left unanswered) and asks the model, without tools, to finish.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "react_agent.py")


def tool_calls_this_run(messages: list) -> int:
    """Tool calls already EXECUTED since the last user message."""
    count = 0
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            break
        count += isinstance(message, ToolMessage)
    return count


def build_agent(llm, max_tool_calls: int = 3, tools=base.TOOLS, system: str = base.SYSTEM):
    llm_with_tools = llm.bind_tools(tools)

    def agent(state: MessagesState) -> dict:
        return {"messages": [llm_with_tools.invoke([SystemMessage(content=system)] + state["messages"])]}

    def route(state: MessagesState) -> str:
        requested = len(getattr(state["messages"][-1], "tool_calls", None) or [])
        if not requested:
            return END
        # Would this round go over the budget? Then none of it runs.
        return "tools" if tool_calls_this_run(state["messages"]) + requested <= max_tool_calls else "wrap_up"

    def wrap_up(state: MessagesState) -> dict:
        refused = [ToolMessage(content=f"Not executed: the budget of {max_tool_calls} tool calls is used up.",
                               tool_call_id=call["id"]) for call in state["messages"][-1].tool_calls]
        final = llm.invoke(  # the plain model: no tools bound, so it can only answer
            [SystemMessage(content=system + " You may not call more tools. Answer with what you know, "
                                            "and say clearly what you could not look up.")]
            + state["messages"] + refused)
        return {"messages": refused + [AIMessage(content=final.text)]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
    builder.add_node("wrap_up", wrap_up)
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route, ["tools", "wrap_up", END])
    builder.add_edge("tools", "agent")
    builder.add_edge("wrap_up", END)
    return builder.compile()


def main() -> None:
    llm = get_chat_model(temperature=0)
    question = ("Look up Barako Bold, Mount Apo Sunrise, Benguet Highlands and Decaf Cloud one at a time, "
                "then tell me the total for one bag of each.")
    for budget in (10, 2):
        result = build_agent(llm, max_tool_calls=budget).invoke({"messages": [("user", question)]})
        executed = tool_calls_this_run(result["messages"][:-1])
        refused = sum("Not executed" in str(m.content) for m in result["messages"] if isinstance(m, ToolMessage))
        print(f"\nbudget={budget}: {executed - refused} tool call(s) ran, {refused} refused")
        print("A:", result["messages"][-1].text[:300])


if __name__ == "__main__":
    main()
