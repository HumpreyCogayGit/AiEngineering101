"""EXER009 checks. Run:  uv run python EXER009/check.py"""

import json

from aicourse.check import Checker
from aicourse.fakes import FakeClient
from aicourse.llm import get_openai_client

checker = Checker(__file__)
mod = checker.load("formatting.py")

VALID = json.dumps({"title": "Workshop", "date": "2026-03-14", "start_time": "09:30",
                    "location": "Makati", "attendees": ["Maria"]})


@checker.check("extract_json_mode() requests json_object and parses the reply")
def _():
    fake = FakeClient([VALID])
    out = mod.extract_json_mode(fake, "text")
    assert out["date"] == "2026-03-14"
    assert fake.calls[0]["response_format"] == {"type": "json_object"}


@checker.check("parse_with_repair() returns a model when the first answer is valid")
def _():
    fake = FakeClient([VALID])
    event = mod.parse_with_repair(fake, [{"role": "user", "content": "x"}], mod.Event)
    assert isinstance(event, mod.Event) and len(fake.calls) == 1


@checker.check("parse_with_repair() sends the validation error back and retries")
def _():
    fake = FakeClient(['{"title": "Workshop"}', VALID])
    original = [{"role": "user", "content": "x"}]
    event = mod.parse_with_repair(fake, original, mod.Event)
    assert event.title == "Workshop" and len(fake.calls) == 2
    retry_msgs = fake.calls[1]["messages"]
    assert retry_msgs[-2]["role"] == "assistant"
    assert "date" in retry_msgs[-1]["content"], "the error message should name the missing field"
    assert original == [{"role": "user", "content": "x"}], "don't modify the caller's list"


@checker.check("parse_with_repair() gives up after max_attempts")
def _():
    fake = FakeClient(['{"bad": true}'])
    try:
        mod.parse_with_repair(fake, [{"role": "user", "content": "x"}], mod.Event, max_attempts=2)
    except ValueError:
        assert len(fake.calls) == 2
        return
    raise AssertionError("expected ValueError")


@checker.check("extract_structured() returns an Event with the right facts  [live API]")
def _():
    event = mod.extract_structured(get_openai_client(), mod.SAMPLE_EMAIL)
    assert isinstance(event, mod.Event), type(event)
    assert event.date == "2026-03-14", event.date
    names = {n.lower() for n in event.attendees}
    assert {"maria", "jun", "priya"} <= names, event.attendees


@checker.check("extract_json_mode() returns the expected keys  [live API]")
def _():
    out = mod.extract_json_mode(get_openai_client(), mod.SAMPLE_EMAIL)
    assert {"title", "date", "attendees"} <= set(out), out


checker.run()
