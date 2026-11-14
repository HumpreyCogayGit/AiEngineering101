"""EXER040 checks. Run:  uv run python EXER040/check.py"""

import json

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("context_engineering.py")

ACCOUNT = json.loads(mod.ACCOUNT.read_text(encoding="utf-8"))
CASES = json.loads(mod.CASES.read_text(encoding="utf-8"))
RAW = json.dumps(ACCOUNT, ensure_ascii=False)


@checker.check("count_tokens() and budget_report() count every section, in order, with a total")
def _():
    assert mod.count_tokens("hello world") == len(mod.ENCODING.encode("hello world"))
    assert mod.count_tokens("") == 0
    sections = {"system": "be brief", "tools": "[]", "history": "", "tool_result": "word " * 50}
    report = mod.budget_report(sections)
    assert list(report) == mod.SECTION_ORDER + ["total"], list(report)
    assert report["tool_result"] == mod.count_tokens("word " * 50) and report["history"] == 0, report
    assert report["total"] == sum(report[name] for name in mod.SECTION_ORDER), report
    assert mod.budget_report({"system": "x"})["tools"] == 0, "a missing section counts as 0 tokens"


@checker.check("fit_to_budget() keeps whole sections in order, cuts the first that overflows, empties the rest")
def _():
    sections = {"system": "one two three", "tools": "four five", "history": "word " * 200, "tool_result": "late"}
    budget = mod.count_tokens("one two three") + mod.count_tokens("four five") + 60
    fitted = mod.fit_to_budget(sections, budget)
    assert fitted["system"] == sections["system"] and fitted["tools"] == sections["tools"], fitted
    assert fitted["history"].endswith(mod.CUT_MARKER), "a cut section must say that it was cut"
    assert fitted["history"].startswith("word word"), "cut from the END, keep the start"
    assert fitted["tool_result"] == "", "sections after the cut one get no room"
    assert mod.budget_report(fitted)["total"] <= budget, mod.budget_report(fitted)
    assert mod.fit_to_budget(sections, 10_000) == sections, "everything fits: nothing changes"
    raw_cut = mod.fit_to_budget(mod.base_sections(RAW), 4000)
    assert mod.budget_report(raw_cut)["total"] <= 4000


@checker.check("compact_orders() keeps one line per order with what support needs, in a fraction of the tokens")
def _():
    text = mod.compact_orders(ACCOUNT)
    lines = text.splitlines()
    assert len(lines) == len(ACCOUNT["orders"]) + 1, f"a header line plus one line per order, got {len(lines)}"
    assert "Bayani Café" in lines[0] and "acct_88213" in lines[0] and "Marco Reyes" in lines[0], lines[0]
    line = next(line for line in lines if line.startswith("N-5104"))
    order = next(o for o in ACCOUNT["orders"] if o["order_id"] == "N-5104")
    for part in (order["created_at"][:10], "delivered", "12x Barako Bold", "1x Hand Grinder Pro",
                 str(order["totals"]["grand_total"]), order["shipping"]["carrier"],
                 order["shipping"]["tracking_number"], "signed by L. Navarro", "Makati"):
        assert part in line, f"{part!r} missing from: {line}"
    assert "burr" in next(line for line in lines if line.startswith("N-5126")), "the last event explains the return"
    assert "warehouse_bin" not in text and "B-0" not in text, "internal fields support never needs are dropped"
    assert mod.count_tokens(text) < mod.count_tokens(RAW) / 5, (mod.count_tokens(text), mod.count_tokens(RAW))


@checker.check("run_subagent() reads the material in its own context and returns findings and its token cost")
def _():
    llm = fake_chat_model("  Order N-5121 was cancelled.  ")
    findings, used = mod.run_subagent(llm, "Which order was cancelled?", "MATERIAL-XYZ")
    assert findings == "Order N-5121 was cancelled.", repr(findings)
    sent = llm.received[0]
    assert len(sent) == 2 and sent[0].type == "system" and sent[0].content == mod.SUBAGENT_PROMPT, sent
    assert "MATERIAL-XYZ" in sent[1].content and "Which order was cancelled?" in sent[1].content, sent[1].content
    expected = sum(mod.count_tokens(m.content) + 4 for m in sent) + mod.count_tokens(findings)
    assert used == expected, f"tokens used: {used}, expected input + answer = {expected}"


@checker.check("needle_context() places the needle at the start, in the middle or at the end of n distractors")
def _():
    noise = [f"note {i}" for i in range(10)]
    assert mod.needle_context("NEEDLE", noise, 0, "middle") == ["NEEDLE"]
    start, middle, end = (mod.needle_context("NEEDLE", noise, 6, p) for p in ("start", "middle", "end"))
    assert len(start) == len(middle) == len(end) == 7, "n distractors plus the needle"
    assert start.index("NEEDLE") == 0 and middle.index("NEEDLE") == 3 and end.index("NEEDLE") == 6
    assert [n for n in middle if n != "NEEDLE"] == noise[:6], "the first n distractors, in order"
    assert noise == [f"note {i}" for i in range(10)], "the distractor list must not be changed"


@checker.check("evaluate() reports accuracy, main and total tokens per call, and the misses")
def _():
    llm = fake_chat_model("Order N-5121 was cancelled; the total was 7,600 PHP.")
    probes = [{"question": "Which order was cancelled?", "expect_keywords": ["N-5121"]},
              {"question": "Grand total?", "expect_keywords": ["7600"]},
              {"question": "Where is it?", "expect_keywords": ["pasig"]}]
    sections = {"system": "be brief", "tool_result": "data"}
    result = mod.evaluate(llm, lambda q: (sections, 100), probes)
    main = mod.count_message_tokens(mod.build_messages(sections, "Where is it?"))
    assert result["accuracy"] == 2 / 3, result
    assert result["missed"] == ["Where is it?"], result
    assert abs(result["main_tokens"] - main) <= 2, (result, main)
    assert result["total_tokens"] == result["main_tokens"] + 100, "total = main call + tokens spent elsewhere"
    assert llm.received[0][-1].content.endswith("Question: Which order was cancelled?"), "the question goes last"


@checker.check("compacting keeps the answers that cutting loses; a sub-agent keeps the main call small  [live API]")
def _():
    llm = get_chat_model(temperature=0)
    results = {name: mod.evaluate(llm, builder, CASES["probes"])
               for name, builder in mod.build_strategies(llm, ACCOUNT).items()}
    raw, cut, compact, sub = results.values()
    assert compact["accuracy"] >= 5 / 6, results
    assert cut["accuracy"] < compact["accuracy"], "cutting the raw response loses the later orders"
    assert compact["main_tokens"] < raw["main_tokens"] / 4, results
    assert sub["accuracy"] >= 4 / 6, results
    assert sub["main_tokens"] < raw["main_tokens"] / 10, results
    assert sub["total_tokens"] > raw["main_tokens"], "the sub-agent still reads the raw response: isolation moves tokens"


checker.run()
