"""EXER035 checks (offline, fake model with token usage). Run:  uv run python EXER035/check.py"""

from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model

checker = Checker(__file__)
mod = checker.load("observability.py")


def usage(i, o):
    return {"input_tokens": i, "output_tokens": o, "total_tokens": i + o}


@tool
def lookup(q: str) -> str:
    """Look something up."""
    return "found it"


@tool
def broken(q: str) -> str:
    """Always fails."""
    raise ConnectionError("service down")


def run_agent(tools, *replies):
    tracker = mod.UsageTracker()
    agent = create_agent(fake_chat_model(*replies), tools)
    agent.invoke({"messages": [("user", "hi")]}, {"callbacks": [tracker]})
    return tracker


TOOL_THEN_ANSWER = (
    AIMessage(content="", tool_calls=[{"name": "lookup", "args": {"q": "x"}, "id": "1"}], usage_metadata=usage(1000, 50)),
    AIMessage(content="done", usage_metadata=usage(1200, 100)),
)


@checker.check("on_llm_end() records tokens for every model call")
def _():
    tracker = run_agent([lookup], *TOOL_THEN_ANSWER)
    llm_spans = [s for s in tracker.spans.values() if s.kind == "llm"]
    assert [(s.input_tokens, s.output_tokens) for s in llm_spans] == [(1000, 50), (1200, 100)]
    assert all(s.end is not None for s in llm_spans)
    assert llm_spans[0].detail == "→ calls lookup", llm_spans[0].detail


@checker.check("tool calls become spans with a duration")
def _():
    tracker = run_agent([lookup], *TOOL_THEN_ANSWER)
    tool_spans = [s for s in tracker.spans.values() if s.kind == "tool"]
    assert [s.name for s in tool_spans] == ["lookup"] and tool_spans[0].end is not None


@checker.check("tool errors are recorded on the span")
def _():
    tracker = mod.UsageTracker()
    agent = create_agent(fake_chat_model(
        AIMessage(content="", tool_calls=[{"name": "broken", "args": {"q": "x"}, "id": "1"}]), "sorry"), [broken])
    try:
        agent.invoke({"messages": [("user", "hi")]}, {"callbacks": [tracker]})
    except Exception:
        pass  # whether the agent survives a tool error depends on its settings; the span must record it
    errors = [s.error for s in tracker.spans.values() if s.error]
    assert errors and "ConnectionError" in errors[0], errors


@checker.check("report() totals calls, tokens and cost (per-million pricing)")
def _():
    report = run_agent([lookup], *TOOL_THEN_ANSWER).report({"input": 1.0, "output": 10.0})
    assert report["llm_calls"] == 2 and report["tool_calls"] == 1 and report["errors"] == 0, report
    assert report["input_tokens"] == 2200 and report["output_tokens"] == 150
    assert abs(report["cost_usd"] - (2200 * 1.0 + 150 * 10.0) / 1e6) < 1e-12, report["cost_usd"]


@checker.check("timeline() lists spans in order")
def _():
    lines = run_agent([lookup], *TOOL_THEN_ANSWER).timeline()
    assert [line.split()[0] for line in lines] == ["LLM", "TOOL", "LLM"], lines


checker.run()
