"""EXER008 checks. Run:  uv run python EXER008/check.py"""

from aicourse.check import Checker
from aicourse.fakes import FakeClient
from aicourse.llm import get_openai_client

checker = Checker(__file__)
mod = checker.load("prompts.py")


@checker.check("SYSTEM_V2 names every label and mentions the <ticket> delimiter")
def _():
    text = mod.SYSTEM_V2.lower()
    assert text.strip() != "todo", "write SYSTEM_V2"
    missing = [label for label in mod.LABELS if label not in text]
    assert not missing, f"labels missing from SYSTEM_V2: {missing}"
    assert "<ticket>" in text, "tell the model the ticket is inside <ticket> tags"


@checker.check("build_messages_v2() = system + delimited user message")
def _():
    msgs = mod.build_messages_v2("My card was charged twice")
    assert [m["role"] for m in msgs] == ["system", "user"]
    assert "<ticket>" in msgs[1]["content"] and "</ticket>" in msgs[1]["content"]
    assert "My card was charged twice" in msgs[1]["content"]


@checker.check("build_messages_v3() has >= 3 user/assistant example pairs")
def _():
    msgs = mod.build_messages_v3("hello")
    roles = [m["role"] for m in msgs]
    assert roles[0] == "system" and roles[-1] == "user"
    middle = roles[1:-1]
    assert len(middle) >= 6 and middle == ["user", "assistant"] * (len(middle) // 2), roles
    assert all(m["content"] in mod.LABELS for m in msgs if m["role"] == "assistant")


@checker.check("few-shot examples are not copied from the test set")
def _():
    assert len(mod.FEW_SHOT_EXAMPLES) >= 3, "add at least 3 examples"
    test_texts = {row["text"] for row in mod.load_dataset()}
    assert not any(ex in test_texts for ex, _ in mod.FEW_SHOT_EXAMPLES), \
        "never put test data in your prompt — the accuracy would be meaningless"


@checker.check("normalize_label() cleans up messy answers")
def _():
    assert mod.normalize_label("Billing.") == "billing"
    assert mod.normalize_label("  TECHNICAL ") == "technical"
    assert mod.normalize_label("This is an account issue") == "account"
    assert mod.normalize_label("no idea") == "unknown"


@checker.check("classify() uses temperature=0")
def _():
    fake = FakeClient(["billing"])
    assert mod.classify(fake, mod.build_messages_v2("refund please")) == "billing"
    assert fake.calls[0].get("temperature") == 0


@checker.check("v3 (few-shot) accuracy >= 80% on tickets.json  [live API]")
def _():
    acc = mod.evaluate(get_openai_client(), mod.build_messages_v3, mod.load_dataset())
    assert acc >= 0.8, f"accuracy {acc:.0%}"


checker.run()
