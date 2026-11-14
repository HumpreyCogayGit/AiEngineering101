"""EXER038 — Evaluating Agents (starter).

EXER024 scored what a RAG chain SAID. An agent also DOES things: it calls
tools, in some order, with some arguments. Two agents can give the same
answer, one by looking the price up and one by guessing it. Only the first
will be right tomorrow. The list of tool calls an agent made is its
TRAJECTORY, and this exercise scores it on three questions:

    tools      did it call the right tools: none missing, none extra?
    order      did the calls happen in a workable order?
    arguments  did each call get the right arguments?

Everything here is plain code: no LLM judge is needed to compare tool calls.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.messages import AIMessage, BaseMessage

EXERCISE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EXERCISE))  # for agent_under_test.py, which sits next to cases.json
from agent_under_test import build_agent, evaluate_expression  # noqa: E402

from aicourse.llm import get_chat_model  # noqa: E402

CASES = EXERCISE / "cases.json"
REPORT = Path(__file__).resolve().parent / "output" / "agent_eval.md"


@dataclass(frozen=True)
class Call:
    """One tool call: the tool's name and the arguments it was given."""

    name: str
    args: dict = field(default_factory=dict, hash=False, compare=True)


# ------------------------------------------------------------------ 1. the trajectory
def extract_trajectory(messages: list[BaseMessage]) -> list[Call]:
    """Every tool call the agent made, in the order it made them.

    Walk the messages. Only AIMessages carry tool calls, in `message.tool_calls`:
    a list of dicts with "name" and "args". Return one Call(name, args) per tool call.
    A message can hold several calls (parallel tool calls): keep them all, in order.
    """
    # TODO
    raise NotImplementedError("extract_trajectory")


# ------------------------------------------------------------------ 2. right tools
def missing_and_extra(actual: list[str], expected: list[str]) -> tuple[list[str], list[str]]:
    """Compare tool NAMES as multisets. Returns (missing, extra).

    missing = expected names the agent did not call
    extra   = calls the agent made that were not expected
    Counts matter: expected ["lookup", "lookup"] and actual ["lookup"] -> one "lookup" is missing.
    Hint: copy `actual` into a list, and remove one entry for every expected name you find in it.
    What is left over at the end is the extra calls.
    """
    # TODO
    raise NotImplementedError("missing_and_extra")


# ------------------------------------------------------------------ 3. right order
def in_order(actual: list[str], expected: list[str]) -> bool:
    """True when `expected` is a SUBSEQUENCE of `actual`.

    The expected names must appear in `actual` in the same relative order; other calls may sit
    in between.   in_order(["a", "x", "b"], ["a", "b"]) -> True     in_order(["b", "a"], ["a", "b"]) -> False
    An empty `expected` is always in order.
    Hint: walk `actual` once, keeping the position of the next expected name you are waiting for.
    """
    # TODO
    raise NotImplementedError("in_order")


# ------------------------------------------------------------------ 4. right arguments
def value_matches(actual: object, expected: object) -> bool:
    """Compare one argument value. Models vary in spelling, so compare meaning, not characters.

    expected = {"evaluates_to": 2210}   the actual value is an expression with that result
    expected = a number                 equal within a small tolerance (2210 == 2210.0 == "2210")
    expected = anything else            equal as text, ignoring case and surrounding spaces
    """
    if isinstance(expected, dict) and "evaluates_to" in expected:
        try:
            return abs(evaluate_expression(str(actual)) - expected["evaluates_to"]) < 1e-6
        except (ValueError, ZeroDivisionError):
            return False
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        try:
            return abs(float(actual) - expected) < 1e-6
        except (TypeError, ValueError):
            return False
    return str(actual).strip().lower() == str(expected).strip().lower()


def args_match(actual: dict, expected: dict) -> bool:
    """Every EXPECTED argument is present in `actual` with a matching value.

    Use value_matches(actual_value, expected_value) for each one (it is given, above).
    Arguments the agent passed that the case does not mention are tolerated.
    """
    # TODO
    raise NotImplementedError("args_match")


def unmatched_calls(actual: list[Call], expected: list[Call]) -> list[Call]:
    """Expected calls for which no actual call has the same name AND matching arguments.

    Each actual call can satisfy one expected call only.
    """
    unused = list(actual)
    unmatched: list[Call] = []
    for want in expected:
        found = next((got for got in unused if got.name == want.name and args_match(got.args, want.args)), None)
        if found is None:
            unmatched.append(want)
        else:
            unused.remove(found)
    return unmatched


# ------------------------------------------------------------------ 5. one score
def score_trajectory(actual: list[Call], expected: list[Call]) -> dict:
    """Score one run. Return {"tools": bool, "order": bool, "arguments": bool, "problems": [str, ...]}.

    tools      no missing and no extra calls            -> missing_and_extra() on the names
    order      the expected names are a subsequence      -> in_order() on the names
    arguments  every expected call has a matching call   -> unmatched_calls() (given) returns none
    problems   one readable line per thing that is wrong, e.g. "missing call: calculator",
               "extra call: lookup_product", "wrong arguments for lookup_product: expected {...}"
               (a report that says only "FAIL" does not help anyone fix the agent)
    """
    # TODO
    raise NotImplementedError("score_trajectory")


def answer_ok(answer: str, keywords: list[str]) -> bool:
    text = answer.lower().replace(",", "")
    return all(keyword.lower() in text for keyword in keywords)


# ------------------------------------------------------------------ 6. the run
def run_case(agent, case: dict) -> dict:
    result = agent.invoke({"messages": [("user", case["question"])]})
    actual = extract_trajectory(result["messages"])
    expected = [Call(c["name"], c.get("args", {})) for c in case["expected"]]
    score = score_trajectory(actual, expected)
    answer = result["messages"][-1].text
    score["answer"] = answer_ok(answer, case.get("expect_keywords", []))
    if not score["answer"]:
        score["problems"].append(f"answer lacks {case['expect_keywords']}")
    return {"question": case["question"], "trajectory": actual, "answer_text": answer,
            "passed": all(score[k] for k in ("tools", "order", "arguments", "answer")), **score}


def summarize(rows: list[dict]) -> dict:
    """The share of cases that passed each check, and all of them together.

    Return {"cases": n, "tools": 0..1, "order": 0..1, "arguments": 0..1, "answer": 0..1, "pass_rate": 0..1}.
    Each row has the booleans "tools", "order", "arguments", "answer" and "passed".
    """
    # TODO
    raise NotImplementedError("summarize")


def write_report(rows: list[dict], summary: dict, path: Path = REPORT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Agent evaluation", "", "| Metric | Value |", "|---|---|"]
    lines += [f"| {key} | {value:.0%} |" if isinstance(value, float) else f"| {key} | {value} |"
              for key, value in summary.items()]
    lines += ["", "| | Question | Trajectory | Problems |", "|---|---|---|---|"]
    for r in rows:
        steps = " → ".join(f"{c.name}({', '.join(str(v) for v in c.args.values())})" for c in r["trajectory"]) or "(no tools)"
        lines.append(f"| {'✅' if r['passed'] else '❌'} | {r['question']} | {steps} | {'; '.join(r['problems'])} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    agent = build_agent(get_chat_model(temperature=0))
    rows = []
    for case in cases:
        row = run_case(agent, case)
        rows.append(row)
        steps = " -> ".join(c.name for c in row["trajectory"]) or "(no tools)"
        print(f"{'PASS' if row['passed'] else 'FAIL'}  {case['question'][:58]:<58} {steps}")
        for problem in row["problems"]:
            print(f"        {problem}")
    summary = summarize(rows)
    print("\n" + json.dumps(summary, indent=2))
    print("Report written to", write_report(rows, summary))


if __name__ == "__main__":
    main()
