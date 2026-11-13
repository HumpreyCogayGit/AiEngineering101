"""EXER007 checks. Run:  uv run python EXER007/check.py"""

import inspect

from aicourse.check import Checker
from aicourse.fakes import FakeClient
from aicourse.llm import get_llm_client

checker = Checker(__file__)
mod = checker.load("streaming.py")


@checker.check("stream_reply() is a generator that yields pieces")
def _():
    gen = mod.stream_reply(FakeClient(stream_text="one two three"), [{"role": "user", "content": "x"}])
    assert inspect.isgenerator(gen), "use `yield` inside stream_reply"
    assert list(gen) == ["one", " two", " three"]


@checker.check("stream_reply() requests stream=True")
def _():
    fake = FakeClient()
    list(mod.stream_reply(fake, [{"role": "user", "content": "x"}]))
    assert fake.calls[0].get("stream") is True


@checker.check("collect() joins pieces and calls on_token for each")
def _():
    seen = []
    assert mod.collect(iter(["a", "b", "c"]), seen.append) == "abc"
    assert seen == ["a", "b", "c"]
    assert mod.collect(iter(["x", "y"])) == "xy"


@checker.check("stream_with_usage() returns text and the usage chunk")
def _():
    fake = FakeClient(stream_text="hi there")
    text, usage = mod.stream_with_usage(fake, [{"role": "user", "content": "x"}])
    assert text == "hi there", text
    assert usage.get("total_tokens") == 15, usage
    assert fake.calls[0].get("stream_options") == {"include_usage": True}


@checker.check("real streaming delivers several chunks  [live API]")
def _():
    pieces = list(mod.stream_reply(get_llm_client(),
                                   [{"role": "user", "content": "Count from 1 to 20, separated by spaces."}]))
    assert len(pieces) > 3, f"only {len(pieces)} chunks"
    assert "20" in "".join(pieces)


checker.run()
