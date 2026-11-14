"""EXER038 checks. Run:  uv run python EXER038/check.py"""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("trajectory_eval.py")
Call = mod.Call


def calls(*specs):
    return AIMessage(content="", tool_calls=[{"name": n, "args": a, "id": f"c{i}"} for i, (n, a) in enumerate(specs)])


@checker.check("extract_trajectory() lists every tool call in order, including parallel calls")
def _():
    messages = [
        HumanMessage("total?"),
        calls(("lookup_product", {"name": "Barako Bold"}), ("lookup_product", {"name": "Decaf Cloud"})),
        ToolMessage("x", tool_call_id="c0"), ToolMessage("y", tool_call_id="c1"),
        calls(("calculator", {"expression": "390 + 550"})),
        ToolMessage("940", tool_call_id="c0"),
        AIMessage("It is 940."),
    ]
    trajectory = mod.extract_trajectory(messages)
    assert [c.name for c in trajectory] == ["lookup_product", "lookup_product", "calculator"], trajectory
    assert trajectory[1].args == {"name": "Decaf Cloud"} and trajectory[2].args == {"expression": "390 + 550"}
    assert mod.extract_trajectory([HumanMessage("hi"), AIMessage("hello")]) == []


@checker.check("missing_and_extra() compares tool names as multisets")
def _():
    assert mod.missing_and_extra(["a", "b"], ["a", "b"]) == ([], [])
    assert mod.missing_and_extra(["a"], ["a", "b"]) == (["b"], [])
    assert mod.missing_and_extra(["a", "b", "b"], ["a", "b"]) == ([], ["b"])
    assert mod.missing_and_extra(["a"], ["a", "a"]) == (["a"], []), "counts matter: one of two expected calls is missing"
    assert mod.missing_and_extra(["x"], []) == ([], ["x"])


@checker.check("in_order() accepts a subsequence and rejects a swapped order")
def _():
    assert mod.in_order(["lookup", "lookup", "calc"], ["lookup", "calc"])
    assert mod.in_order(["lookup", "hours", "calc"], ["lookup", "calc"]), "extra calls in between are allowed"
    assert not mod.in_order(["calc", "lookup"], ["lookup", "calc"])
    assert not mod.in_order(["lookup"], ["lookup", "calc"])
    assert mod.in_order([], []) and mod.in_order(["calc"], [])


@checker.check("args_match() compares meaning: case, numbers and expressions")
def _():
    assert mod.args_match({"name": " barako bold "}, {"name": "Barako Bold"})
    assert not mod.args_match({"name": "Decaf Cloud"}, {"name": "Barako Bold"})
    assert mod.args_match({"expression": "3*390 + 2*520"}, {"expression": {"evaluates_to": 2210}})
    assert mod.args_match({"expression": "1170 + 1040"}, {"expression": {"evaluates_to": 2210}})
    assert not mod.args_match({"expression": "3*390"}, {"expression": {"evaluates_to": 2210}})
    assert not mod.args_match({}, {"name": "Barako Bold"}), "a missing argument does not match"
    assert mod.args_match({"name": "Barako Bold", "note": "x"}, {"name": "Barako Bold"}), "extra arguments are tolerated"


@checker.check("score_trajectory() passes a correct run and names each kind of mistake")
def _():
    expected = [Call("lookup_product", {"name": "Barako Bold"}), Call("calculator", {"expression": {"evaluates_to": 780}})]
    good = mod.score_trajectory(
        [Call("lookup_product", {"name": "barako bold"}), Call("calculator", {"expression": "2 * 390"})], expected)
    assert good["tools"] and good["order"] and good["arguments"] and good["problems"] == [], good

    guessed = mod.score_trajectory([], expected)  # the agent answered from memory
    assert not guessed["tools"] and len(guessed["problems"]) >= 2, guessed

    extra = mod.score_trajectory(
        [Call("lookup_product", {"name": "Barako Bold"}), Call("store_hours", {"branch": "BGC"}),
         Call("calculator", {"expression": "2 * 390"})], expected)
    assert not extra["tools"] and extra["order"] and extra["arguments"], extra
    assert any("store_hours" in p for p in extra["problems"]), extra["problems"]

    swapped = mod.score_trajectory(
        [Call("calculator", {"expression": "2 * 390"}), Call("lookup_product", {"name": "Barako Bold"})], expected)
    assert swapped["tools"] and not swapped["order"], swapped

    wrong_bean = mod.score_trajectory(
        [Call("lookup_product", {"name": "Decaf Cloud"}), Call("calculator", {"expression": "2 * 390"})], expected)
    assert wrong_bean["tools"] and wrong_bean["order"] and not wrong_bean["arguments"], wrong_bean
    assert any("lookup_product" in p for p in wrong_bean["problems"]), wrong_bean["problems"]


@checker.check("summarize() reports the share of cases that passed each check")
def _():
    rows = [
        {"tools": True, "order": True, "arguments": True, "answer": True, "passed": True},
        {"tools": False, "order": True, "arguments": False, "answer": True, "passed": False},
        {"tools": True, "order": True, "arguments": True, "answer": False, "passed": False},
        {"tools": True, "order": True, "arguments": True, "answer": True, "passed": True},
    ]
    summary = mod.summarize(rows)
    assert summary["cases"] == 4 and summary["tools"] == 0.75 and summary["order"] == 1.0
    assert summary["arguments"] == 0.75 and summary["answer"] == 0.75 and summary["pass_rate"] == 0.5, summary


@checker.check("run_case() catches an agent that gives the right answer without using its tools")
def _():
    case = {"question": "How much is one bag of Barako Bold?",
            "expected": [{"name": "lookup_product", "args": {"name": "Barako Bold"}}], "expect_keywords": ["390"]}
    honest = mod.build_agent(fake_chat_model(calls(("lookup_product", {"name": "Barako Bold"})), "It costs ₱390."))
    row = mod.run_case(honest, case)
    assert row["passed"], row["problems"]
    guesser = mod.build_agent(fake_chat_model("It costs ₱390."))  # same answer, no lookup
    row = mod.run_case(guesser, case)
    assert row["answer"] and not row["tools"] and not row["passed"], row


@checker.check("the real agent passes at least 4 of the 6 cases  [live API]")
def _():
    import json

    cases = json.loads(mod.CASES.read_text(encoding="utf-8"))
    agent = mod.build_agent(get_chat_model(temperature=0))
    rows = [mod.run_case(agent, case) for case in cases]
    summary = mod.summarize(rows)
    failed = [(r["question"], r["problems"]) for r in rows if not r["passed"]]
    assert summary["pass_rate"] >= 4 / 6, failed


checker.run()
