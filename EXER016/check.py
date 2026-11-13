"""EXER016 checks. Run:  uv run python EXER016/check.py"""

import json

from aicourse.check import Checker
from aicourse.fakes import FakeClient
from aicourse.llm import get_openai_client

checker = Checker(__file__)
mod = checker.load("tools_raw.py")


@checker.check("TOOLS describes get_weather and calculate with JSON schemas")
def _():
    names = {t["function"]["name"] for t in mod.TOOLS}
    assert names == {"get_weather", "calculate"}, names
    for t in mod.TOOLS:
        fn = t["function"]
        assert t["type"] == "function" and fn["description"], fn["name"]
        assert fn["parameters"]["type"] == "object" and fn["parameters"]["required"], fn["name"]


@checker.check("run_tool() executes a tool and returns JSON")
def _():
    assert json.loads(mod.run_tool("calculate", '{"expression": "2 + 3 * 4"}')) == 14
    assert json.loads(mod.run_tool("get_weather", '{"city": "Tokyo"}'))["temp_c"] == 18


@checker.check("run_tool() returns errors instead of raising")
def _():
    assert "error" in json.loads(mod.run_tool("launch_rocket", "{}"))
    assert "error" in json.loads(mod.run_tool("calculate", '{"expression": "__import__(\'os\')"}'))
    assert "error" in json.loads(mod.run_tool("calculate", "not json"))


@checker.check("run_conversation() runs the loop: tool call -> tool result -> answer")
def _():
    fake = FakeClient([
        {"tool_calls": [{"id": "call_1", "name": "calculate", "arguments": {"expression": "6*7"}}]},
        "The answer is 42.",
    ])
    assert mod.run_conversation(fake, "what is 6*7?") == "The answer is 42."
    assert len(fake.calls) == 2
    second = fake.calls[1]["messages"]
    assert second[-2]["role"] == "assistant" and second[-2]["tool_calls"], "keep the assistant tool request"
    assert second[-1] == {"role": "tool", "tool_call_id": "call_1", "content": "42"}, second[-1]
    assert fake.calls[0].get("tools"), "send TOOLS with the request"


@checker.check("run_conversation() stops after max_rounds")
def _():
    fake = FakeClient([{"tool_calls": [{"id": "c", "name": "calculate", "arguments": {"expression": "1"}}]}])
    out = mod.run_conversation(fake, "loop forever", max_rounds=3)
    assert len(fake.calls) == 3 and isinstance(out, str)


@checker.check("the model uses the calculator for exact math  [live API]")
def _():
    answer = mod.run_conversation(get_openai_client(), "What is 1234 * 5678? Use the calculator.")
    assert "7006652" in answer.replace(",", "").replace(" ", ""), answer


checker.run()
