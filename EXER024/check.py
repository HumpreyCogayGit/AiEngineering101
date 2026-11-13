"""EXER024 checks. Run:  uv run python EXER024/check.py"""

from pydantic import ValidationError

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("evaluate.py")


@checker.check("reciprocal_rank() = 1/position of the first correct source")
def _():
    assert mod.reciprocal_rank(["a", "b", "c"], "a") == 1.0
    assert mod.reciprocal_rank(["a", "b", "b"], "b") == 0.5
    assert mod.reciprocal_rank(["a", "b"], "z") == 0.0


@checker.check("Grade has reasoning + score, and rejects scores outside 1-5")
def _():
    if not mod.Grade.model_fields:
        raise NotImplementedError("Grade fields")
    assert list(mod.Grade.model_fields)[:2] == ["reasoning", "score"], "reasoning must come before score"
    mod.Grade(reasoning="ok", score=5)
    for bad in (0, 6):
        try:
            mod.Grade(reasoning="x", score=bad)
        except ValidationError:
            continue
        raise AssertionError(f"score={bad} should be rejected")


@checker.check("CORRECTNESS_PROMPT has {question}, {reference}, {answer}")
def _():
    text = mod.CORRECTNESS_PROMPT
    assert text.strip() != "TODO", "write CORRECTNESS_PROMPT"
    text.format(question="q", reference="r", answer="a")  # raises KeyError if a variable is wrong
    for var in ("{question}", "{reference}", "{answer}"):
        assert var in text, var


@checker.check("judge() returns a Grade from the judge model")
def _():
    grade = mod.Grade(reasoning="fine", score=4)
    assert mod.judge(fake_chat_model(structured=[grade]), "prompt") == grade


@checker.check("summarize() aggregates answerable and unanswerable rows")
def _():
    rows = [
        {"hit": True, "rr": 1.0, "faithfulness": 5, "correctness": 4},
        {"hit": False, "rr": 0.0, "faithfulness": 3, "correctness": 2},
        {"hit": None, "rr": None, "faithfulness": 5, "correctness": 5, "refused_correctly": True},
    ]
    s = mod.summarize(rows)
    assert s["questions"] == 3 and s["hit_rate"] == 0.5 and s["mrr"] == 0.5, s
    assert abs(s["faithfulness"] - 13 / 3) < 1e-9 and abs(s["correctness"] - 11 / 3) < 1e-9, s
    assert s["refusal_rate"] == 1.0


@checker.check("the judge spots an unfaithful answer  [live API]")
def _():
    judge_llm = get_chat_model(temperature=0)
    context = "[1] Standard shipping is free for orders over 1,500 pesos."
    good = mod.judge_faithfulness(judge_llm, "Is shipping free?", context, "Yes, for orders over ₱1,500 [1].")
    bad = mod.judge_faithfulness(judge_llm, "Is shipping free?", context, "Yes, shipping is always free worldwide, even to Mars.")
    assert good.score >= 4 and bad.score <= 2, (good, bad)


checker.run()
