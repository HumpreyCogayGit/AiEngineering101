"""EXER027 checks. Run:  uv run python EXER027/check.py"""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("react_agent.py")


def calls(*specs):
    return AIMessage(content="", tool_calls=[{"name": n, "args": a, "id": f"c{i}"} for i, (n, a) in enumerate(specs)])


@checker.check("should_continue() routes to tools only when tools are requested")
def _():
    assert mod.should_continue({"messages": [calls(("calculator", {"expression": "1"}))]}) == "tools"
    assert mod.should_continue({"messages": [AIMessage(content="done")]}) == "__end__"


@checker.check("the graph has an agent node and a tools node")
def _():
    nodes = set(mod.build_agent(fake_chat_model("x")).get_graph().nodes)
    assert {"agent", "tools"} <= nodes, nodes


@checker.check("the agent loops: agent -> tools -> agent -> tools -> agent -> answer")
def _():
    llm = fake_chat_model(
        calls(("lookup_product", {"name": "Barako Bold"}), ("lookup_product", {"name": "Mount Apo Sunrise"})),
        calls(("calculator", {"expression": "3*390 + 2*520"})),
        "The total is ₱2,210.",
    )
    result = mod.build_agent(llm).invoke({"messages": [("user", "total?")]})
    kinds = [type(m).__name__ for m in result["messages"]]
    assert kinds == ["HumanMessage", "AIMessage", "ToolMessage", "ToolMessage",
                     "AIMessage", "ToolMessage", "AIMessage"], kinds
    assert result["messages"][5].content in ("2210", "2210.0"), result["messages"][5].content
    assert len(llm.bound_tools) == 3


@checker.check("the system prompt is sent but not stored in the state")
def _():
    llm = fake_chat_model("hi")
    result = mod.build_agent(llm, system="SYSTEM-XYZ").invoke({"messages": [HumanMessage("hello")]})
    assert llm.received[0][0].content == "SYSTEM-XYZ"
    assert not any("SYSTEM-XYZ" in m.text for m in result["messages"])


@checker.check("run() stops a runaway loop with the recursion limit")
def _():
    llm = fake_chat_model(calls(("current_time", {})))  # always asks for a tool, forever
    answer = mod.run(mod.build_agent(llm), "loop", recursion_limit=6)
    assert isinstance(answer, str) and "couldn't" in answer.lower(), answer


@checker.check("the agent computes an order total with tools  [live API]")
def _():
    graph = mod.build_agent(get_chat_model(temperature=0))
    result = graph.invoke({"messages": [("user", "Total price of 3 bags of Barako Bold and 2 of Mount Apo Sunrise?")]})
    assert any(isinstance(m, ToolMessage) for m in result["messages"])
    assert "2210" in result["messages"][-1].text.replace(",", ""), result["messages"][-1].text


checker.run()
