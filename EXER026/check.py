"""EXER026 checks (offline). Run:  uv run python EXER026/check.py"""

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("ticket_graph.py")


@checker.check("classify() and prioritize() return partial state updates")
def _():
    assert mod.classify({"ticket": "Please send my invoice"}) == {"category": "billing", "steps": ["classify"]}
    assert mod.classify({"ticket": "Hello there"})["category"] == "general"
    assert mod.prioritize({"ticket": "URGENT help"}) == {"priority": "high", "steps": ["prioritize"]}


@checker.check("TicketState.steps uses a reducer (Annotated with operator.add)")
def _():
    hints = mod.TicketState.__annotations__
    assert "steps" in hints, "add the steps key"
    assert "operator.add" in str(hints["steps"]) or "add" in repr(getattr(hints["steps"], "__metadata__", "")), hints["steps"]


@checker.check("the graph has all six nodes")
def _():
    nodes = set(mod.build_graph().get_graph().nodes)
    expected = {"classify", "prioritize", "billing", "technical", "general", "escalate"}
    assert expected <= nodes, f"missing: {expected - nodes}"


@checker.check("a normal technical ticket: classify -> prioritize -> technical")
def _():
    out = mod.build_graph().invoke({"ticket": "The app crashes on start"})
    assert out["category"] == "technical" and out["priority"] == "normal"
    assert out["steps"] == ["classify", "prioritize", "technical"], out["steps"]


@checker.check("an urgent billing ticket is escalated")
def _():
    out = mod.build_graph().invoke({"ticket": "I was charged twice, refund ASAP"})
    assert out["steps"] == ["classify", "prioritize", "billing", "escalate"], out["steps"]
    assert out["response"].endswith("A supervisor has been notified.")


@checker.check("stream_mode='updates' yields one update per node")
def _():
    updates = list(mod.build_graph().stream({"ticket": "Do you have a store in Cebu?"}, stream_mode="updates"))
    assert [list(u)[0] for u in updates] == ["classify", "prioritize", "general"], updates


checker.run()
