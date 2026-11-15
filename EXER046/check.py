"""EXER046 checks. Run:  uv run python EXER046/check.py

Offline checks use fake models and made-up measurements. The live check runs the task suite
on your configured model.
"""

from datetime import date

import httpx
import openai
from langchain_core.messages import AIMessage

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model

checker = Checker(__file__)
mod = checker.load("routing.py")


def row(task, correct, seconds=1.0, tin=100, tout=10, error=None):
    return {"task": task, "correct": correct, "seconds": seconds, "input_tokens": tin, "output_tokens": tout,
            "error": error, "output": None}


@checker.check("parse_candidates() reads 'model' and 'model@effort'")
def _():
    a, b = mod.parse_candidates(" gemma4:e4b , my-deploy@low ")
    assert (a.name, a.model, a.reasoning_effort) == ("gemma4:e4b", "gemma4:e4b", None)
    assert (b.name, b.model, b.reasoning_effort) == ("my-deploy@low", "my-deploy", "low")


@checker.check("summarize(): accuracy per task, errors, p50/p95 latency, and cost per 1,000 requests")
def _():
    rows = ([row("classify", True)] * 3 + [row("classify", False, error="Timeout")]
            + [row("tool", True, seconds=s) for s in (0.5, 1.5, 2.0, 9.0)])
    s = mod.summarize(rows, {"input": 0.40, "output": 1.60})
    assert s["accuracy"] == {"classify": 0.75, "tool": 1.0}, s["accuracy"]
    assert s["errors"] == 1 and s["p50_seconds"] == 1.0 and s["p95_seconds"] == 9.0, s
    assert abs(s["cost_per_1000"] - 0.056) < 1e-9, s["cost_per_1000"]   # (100*0.40 + 10*1.60) / 1e6 * 1000
    assert mod.summarize(rows, None)["cost_per_1000"] is None, "unknown price -> None, not 0"


@checker.check("choose(): the cheapest candidate that meets every bar; None when none does")
def _():
    summaries = {
        "large": {"accuracy": {"tool": 1.0, "extract": 1.0}, "p95_seconds": 3.0, "cost_per_1000": 2.0},
        "small": {"accuracy": {"tool": 1.0, "extract": 1.0}, "p95_seconds": 2.0, "cost_per_1000": 0.5},
        "tiny": {"accuracy": {"tool": 0.75, "extract": 1.0}, "p95_seconds": 1.0, "cost_per_1000": 0.1},
        "local": {"accuracy": {"tool": 1.0, "extract": 1.0}, "p95_seconds": 12.0, "cost_per_1000": 0.0},
    }
    bars = {"tool": 1.0, "extract": 1.0}
    assert mod.choose(summaries, bars, max_p95=5.0) == "small", "tiny misses a bar, local is too slow"
    assert mod.choose(summaries, bars, max_p95=15.0) == "local"
    assert mod.choose(summaries, {"tool": 1.1}, max_p95=15.0) is None
    unknown = {"x": {"accuracy": {"tool": 1}, "p95_seconds": 1.0, "cost_per_1000": None},
               "y": {"accuracy": {"tool": 1}, "p95_seconds": 2.0, "cost_per_1000": 3.0}}
    assert mod.choose(unknown, {"tool": 1}, 5.0) == "y", "prefer a known price over an unknown one"


@checker.check("route_question(): short factual questions go small; arithmetic, reasons, complaints and long ones go large")
def _():
    for q in ("Is shipping free?", "Do you deliver to Japan?", "When do loyalty stars expire?"):
        assert mod.route_question(q) == "small", q
    for q in ("What do 3 bags of Barako Bold cost in total?", "Why was my order returned?",
              "My grinder arrived broken, what now?", "Is shipping free? And do you ship to Japan?",
              " ".join(["word"] * 26)):
        assert mod.route_question(q) == "large", q


@checker.check("needs_escalation(): empty answers, failed calls, and 'I don't know' after a search")
def _():
    assert mod.needs_escalation({"answer": "Free over ₱1,500.", "tools_used": ["search_knowledge_base"]}) == []
    assert mod.needs_escalation({"answer": "", "tools_used": []})
    assert mod.needs_escalation({"answer": "I don’t know.", "tools_used": ["search_knowledge_base"]})
    assert mod.needs_escalation({"answer": "I don't know who won.", "tools_used": []}) == [], \
        "a refusal without searching is the small model doing its job (an off-topic question)"


@checker.check("RoutedHelpdesk sends easy questions small, hard ones large, and escalates on a quality signal")
def _():
    calls = []

    def small(q, t):
        calls.append(("small", q))
        return {"answer": "I don't know." if "CEO" in q else "Yes.", "tools_used": ["search_knowledge_base"]}

    def large(q, t):
        calls.append(("large", q))
        return {"answer": "Answer.", "tools_used": ["search_knowledge_base"]}

    helpdesk = mod.RoutedHelpdesk(small, large)
    assert helpdesk.ask("Is shipping free?", "t1")["route"] == "small"
    assert helpdesk.ask("What is the total for 3 bags?", "t2")["route"] == "large"
    reply = helpdesk.ask("Who is the CEO?", "t3")
    assert reply["route"] == "small→large" and reply["answer"] == "Answer.", reply
    assert [c[0] for c in calls] == ["small", "large", "small", "large"], calls
    assert helpdesk.log[-1]["escalated"] and helpdesk.log[-1]["reasons"], helpdesk.log[-1]


@checker.check("with_provider_fallback(): a provider error goes to the fallback, a bug in the request does not")
def _():
    request = httpx.Request("POST", "https://provider.invalid/v1/chat/completions")

    class Failing:
        def __init__(self, exc):
            self.exc = exc

        def __call__(self, *_):
            raise self.exc

    from langchain_core.runnables import RunnableLambda

    fallback = fake_chat_model(AIMessage(content="from the fallback"))
    down = RunnableLambda(Failing(openai.APIConnectionError(request=request)))
    assert mod.with_provider_fallback(down, fallback).invoke("hi").text == "from the fallback"
    buggy = RunnableLambda(Failing(ValueError("bad request built by our code")))
    try:
        mod.with_provider_fallback(buggy, fallback).invoke("hi")
    except ValueError:
        pass
    else:
        raise AssertionError("a ValueError is our bug: it must not be hidden by a fallback")


@checker.check("retiring_soon(): models retiring within the window, soonest first, including overdue ones")
def _():
    registry = {"a": {"retires": "2027-01-10"}, "b": {"retires": "2026-12-01"}, "c": {"retires": "2027-06-01"},
                "d": {}, "e": {"retires": "2026-11-01"}}
    assert mod.retiring_soon(registry, date(2026, 11, 15), within_days=90) == [("e", -14), ("b", 16), ("a", 56)]


@checker.check("the task suite runs on your model, and every case produces a result  [live API]")
def _():
    from aicourse.llm import get_chat_model

    llm = get_chat_model(temperature=0)
    cases = mod.suite(limit_tickets=4)
    rows = [mod.run_case(llm, case) for case in cases]
    summary = mod.summarize(rows, None)
    print(f"         {summary}")
    # A model that breaks the schema is a RESULT (an error counted against it), not a crash of the suite.
    assert len(rows) == len(cases) and all(r["seconds"] > 0 for r in rows)
    assert set(summary["accuracy"]) == {"classify", "extract", "tool"}
    assert summary["errors"] < len(rows), [r["error"] for r in rows if r["error"]]


checker.run()
