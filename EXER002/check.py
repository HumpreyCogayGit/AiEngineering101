"""EXER002 checks (offline — no API calls). Run:  uv run python EXER002/check.py"""

from pathlib import Path

from pydantic import ValidationError

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("primer.py")
SAMPLE = Path(__file__).parent / "sample_response.json"


@checker.check("load_response() reads the sample file into a dict")
def _():
    data = mod.load_response(SAMPLE)
    assert isinstance(data, dict) and data["object"] == "chat.completion"


@checker.check("get_reply_text() digs out the assistant text")
def _():
    assert mod.get_reply_text(mod.load_response(SAMPLE)) == "The capital of France is Paris."


@checker.check("get_total_tokens() returns 32 for the sample")
def _():
    assert mod.get_total_tokens(mod.load_response(SAMPLE)) == 32


@checker.check("safe_get_reply() returns None for broken responses")
def _():
    assert mod.safe_get_reply({}) is None
    assert mod.safe_get_reply({"choices": []}) is None
    assert mod.safe_get_reply({"choices": [{"message": None}]}) is None
    assert mod.safe_get_reply(mod.load_response(SAMPLE)) == "The capital of France is Paris."


@checker.check("build_request() without system message")
def _():
    assert mod.build_request("dep", "Hi") == {
        "model": "dep",
        "messages": [{"role": "user", "content": "Hi"}],
    }


@checker.check("build_request() puts the system message first")
def _():
    body = mod.build_request("dep", "Hi", "Be brief.")
    assert body["messages"][0] == {"role": "system", "content": "Be brief."}
    assert body["messages"][1] == {"role": "user", "content": "Hi"}


@checker.check("parse_messages() returns Message objects")
def _():
    msgs = mod.parse_messages([{"role": "user", "content": "Hello"}])
    assert msgs[0].role == "user" and msgs[0].content == "Hello"


@checker.check("parse_messages() rejects an invalid role")
def _():
    try:
        mod.parse_messages([{"role": "robot", "content": "beep"}])
    except ValidationError:
        return
    raise AssertionError("expected a ValidationError for role='robot'")


checker.run()
