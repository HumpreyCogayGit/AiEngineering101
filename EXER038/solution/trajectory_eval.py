"""EXER038 — Evaluating Agents (reference solution).

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
    """Every tool call the agent made, in the order it made them."""
    return [
        Call(call["name"], dict(call["args"]))
        for message in messages
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]


# ------------------------------------------------------------------ 2. right tools
def missing_and_extra(actual: list[str], expected: list[str]) -> tuple[list[str], list[str]]:
    """Compare tool NAMES as multisets: calling a tool twice when once was expected is one extra."""
    remaining = list(actual)
    missing: list[str] = []
    for name in expected:
        if name in remaining:
            remaining.remove(name)
        else:
            missing.append(name)
    return missing, remaining


# ------------------------------------------------------------------ 3. right order
def in_order(actual: list[str], expected: list[str]) -> bool:
    """True when `expected` is a subsequence of `actual`: same relative order, extras allowed in between."""
    position = 0
    for name in actual:
        if position < len(expected) and name == expected[position]:
            position += 1
    return position == len(expected)


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
    """Every expected argument is present with a matching value. Extra arguments are tolerated."""
    return all(key in actual and value_matches(actual[key], value) for key, value in expected.items())


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
    """{"tools", "order", "arguments": bool, "problems": [text, ...]} for one run."""
    actual_names = [c.name for c in actual]
    expected_names = [c.name for c in expected]
    missing, extra = missing_and_extra(actual_names, expected_names)
    wrong_args = unmatched_calls(actual, expected)
    problems = [f"missing call: {name}" for name in missing] + [f"extra call: {name}" for name in extra]
    order_ok = in_order(actual_names, expected_names)
    if not missing and not order_ok:
        problems.append(f"wrong order: {' -> '.join(actual_names)}")
    # A call that is missing altogether is a tools problem, not an arguments problem.
    problems += [f"wrong arguments for {c.name}: expected {c.args}" for c in wrong_args if c.name not in missing]
    return {
        "tools": not missing and not extra,
        "order": order_ok,
        "arguments": not wrong_args,
        "problems": problems,
    }


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
    """The share of cases that passed each check, and all of them together."""
    total = len(rows)
    return {
        "cases": total,
        **{key: sum(r[key] for r in rows) / total for key in ("tools", "order", "arguments", "answer")},
        "pass_rate": sum(r["passed"] for r in rows) / total,
    }


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
