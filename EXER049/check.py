"""EXER049 checks. Run:  uv run python EXER049/check.py

Offline. Small hand-made traces for the rules, and the four weeks in traces.jsonl for the
whole loop. The new cases are scored with the EXER037 reference score_case.
"""

import json

from aicourse.check import Checker
from aicourse.stretch import solution_of

checker = Checker(__file__)
mod = checker.load("feedback_loop.py")


def trace(tid, at, question, thread="a", answer="ok", feedback=None, blocked=False, seconds=2.0, tokens=1000):
    return {"trace_id": tid, "at": f"2026-11-10T10:{at}+00:00", "user_id": "u1", "thread_id": thread,
            "question": question, "answer": answer, "tools_used": [], "tokens": tokens, "seconds": seconds,
            "blocked": blocked, "feedback": feedback}


@checker.check("implicit_signals(): a request for a person, or the same question again within a minute")
def _():
    traces = [
        trace("t1", "00:00", "Can I return opened beans?"),
        trace("t2", "00:30", "what if the beans are opened, can I return them"),     # asked again, 30 s later
        trace("t3", "01:00", "Can I talk to a human please?"),                        # asked for a person
        trace("t4", "00:00", "Is shipping free?", thread="b"),
        trace("t5", "05:00", "Is shipping free to Cebu?", thread="b"),               # 5 minutes later: a new question
        trace("t6", "00:00", "When do stars expire?", thread="c"),
        trace("t7", "00:20", "Thanks! And the BGC hours?", thread="c"),              # quick, but a different topic
    ]
    signals = mod.implicit_signals(traces)
    assert signals == {"t1": ["asked again"], "t2": ["asked for a person"]}, signals


@checker.check("sample_for_review(): every thumbs-down and signal, plus a reproducible random sample of the rest")
def _():
    traces = mod.load_traces()
    signals = mod.implicit_signals(traces)
    queue = mod.sample_for_review(traces, signals, random_k=10, seed=49)
    ids = [t["trace_id"] for t in queue]
    assert len(ids) == len(set(ids)), "no trace twice"
    downs = {t["trace_id"] for t in traces if t["feedback"] == "down"}
    assert downs <= set(ids) and set(signals) <= set(ids), "every flagged trace is in the queue"
    assert sum(t["why"] == ["random sample"] for t in queue) == 10
    assert not any(t["blocked"] or "human" in t["question"].lower() for t in queue), \
        "blocked attacks and the 'talk to a human' messages themselves are not reviewed as answers"
    again = mod.sample_for_review(traces, signals, random_k=10, seed=49)
    assert [t["trace_id"] for t in again] == ids, "the same seed must give the same queue"
    assert [t["trace_id"] for t in mod.sample_for_review(traces, signals, 10, seed=1)] != ids


@checker.check("to_eval_case(): a reviewed failure becomes a capstone case that the EXER037 scoring accepts")
def _():
    t = trace("t9", "00:00", "Can I return opened beans?", answer="Yes, within 30 days.")
    review = {"verdict": "fail", "category": "grounding", "expect_keywords": ["14"], "expect_tools": ["search_knowledge_base"]}
    case = mod.to_eval_case(t, review)
    assert case == {"category": "grounding", "question": "Can I return opened beans?", "expect_keywords": ["14"],
                    "expect_tools": ["search_knowledge_base"], "source": "production:t9"}, case
    assert mod.to_eval_case(t, {"verdict": "ok"}) is None
    evaluate = solution_of("EXER037", "evaluate.py")
    assistant = solution_of("EXER037", "assistant.py")
    assert evaluate.score_case(case, assistant.Reply("Yes, within 30 days.", ["search_knowledge_base"])) == ["missing '14'"]
    assert evaluate.score_case(case, assistant.Reply("Within 14 days, for 50% store credit.", ["search_knowledge_base"])) == []


@checker.check("dedupe(): drops questions already in the evaluation set or repeated in the batch")
def _():
    existing = [{"question": "Is the Maginhawa café open on Mondays?"}]
    cases = [{"question": "is the maginhawa café open on mondays"}, {"question": "Is the BGC café pet friendly?"},
             {"question": "Is the BGC café pet friendly ?"}, {"question": "Do you ship to Japan?"}]
    assert [c["question"] for c in mod.dedupe(cases, existing)] == ["Is the BGC café pet friendly?", "Do you ship to Japan?"]


@checker.check("weekly_metrics(): per ISO week, rates over answered traces, blocked ones left out")
def _():
    traces = [trace("t1", "00:00", "q", feedback="down", answer="I don't know."),
              trace("t2", "01:00", "q", feedback="up", seconds=5.0),
              trace("t3", "02:00", "q"), trace("t4", "03:00", "attack", blocked=True, seconds=0.0)]
    m = mod.weekly_metrics(traces)
    assert list(m) == ["2026-W46"], list(m)
    assert m["2026-W46"] == {"questions": 3, "rated": 2, "thumbs_down_rate": 0.5, "refusal_rate": 0.333,
                             "mean_tokens": 1000, "p95_seconds": 5.0}, m


@checker.check("drift_alerts(): the last week of traces.jsonl raises refusals and latency; quiet weeks raise nothing")
def _():
    metrics = mod.weekly_metrics(mod.load_traces())
    assert len(metrics) == 4
    alerts = mod.drift_alerts(metrics, {"refusal_rate": 0.5, "p95_seconds": 0.3})
    last = list(metrics)[-1]
    assert alerts and all(a.startswith(last) for a in alerts), alerts
    assert any("refusal_rate" in a for a in alerts) and any("p95_seconds" in a for a in alerts), alerts
    flat = {"W1": {"x": 0.1}, "W2": {"x": 0.12}, "W3": {"x": 0.2}}
    assert mod.drift_alerts(flat, {"x": 0.5}) == ["W3: x 0.2 vs 0.11 before"], mod.drift_alerts(flat, {"x": 0.5})


@checker.check("the whole loop: reviewed failures from four weeks become new, unique evaluation cases")
def _():
    traces = mod.load_traces()
    reviews = json.loads(mod.REVIEWS.read_text(encoding="utf-8"))
    by_id = {t["trace_id"]: t for t in traces}
    cases = [c for c in (mod.to_eval_case(by_id[i], r) for i, r in reviews.items()) if c]
    new = mod.dedupe(cases, json.loads(mod.CAPSTONE_EVAL.read_text(encoding="utf-8")))
    assert len(cases) == 18 and len(new) == 7, (len(cases), len(new))
    assert all(c["source"].startswith("production:") and c["expect_keywords"] for c in new)


checker.run()
