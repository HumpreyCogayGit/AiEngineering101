"""EXER017 checks. Run:  uv run python EXER017/check.py"""

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("lc_tools.py")


def tool_call(name, args, id="call_1"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": id}])


@checker.check("convert_currency is a @tool with typed args and a description")
def _():
    t = mod.convert_currency
    if not isinstance(t, BaseTool):
        raise NotImplementedError("decorate convert_currency with @tool")
    assert set(t.args) == {"amount", "from_currency", "to_currency"}, t.args
    assert t.args["amount"].get("type") == "number", "type hint amount as float"
    assert t.description, "add a docstring"


@checker.check("convert_currency converts correctly")
def _():
    out = mod.convert_currency.invoke({"amount": 100, "from_currency": "EUR", "to_currency": "USD"})
    assert "108.00" in out, out


@checker.check("TOOLS contains all three tools, including word_count")
def _():
    names = {t.name for t in mod.TOOLS}
    assert names == {"get_weather", "convert_currency", "word_count"}, names
    assert mod.word_count.invoke({"text": "one two three"}) == 3


@checker.check("run_tool_loop() executes tool calls and returns ToolMessages")
def _():
    llm = fake_chat_model(tool_call("get_weather", {"city": "Tokyo"}), "It is 18°C in Tokyo.")
    answer, messages = mod.run_tool_loop(llm, "weather in Tokyo?")
    assert answer == "It is 18°C in Tokyo."
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 1 and "18" in tool_msgs[0].content
    assert tool_msgs[0].tool_call_id == "call_1"
    assert len(llm.bound_tools) == 3, "bind all TOOLS to the model"


@checker.check("run_tool_loop() answers every call when the model asks for several at once (parallel tool calls)")
def _():
    both = AIMessage(content="", tool_calls=[
        {"name": "get_weather", "args": {"city": "Tokyo"}, "id": "call_a"},
        {"name": "convert_currency", "args": {"amount": 100, "from_currency": "EUR", "to_currency": "USD"}, "id": "call_b"},
    ])
    llm = fake_chat_model(both, "18°C in Tokyo and 100 EUR is 108 USD.")
    answer, messages = mod.run_tool_loop(llm, "weather in Tokyo and 100 EUR in USD?")
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert [m.tool_call_id for m in tool_msgs] == ["call_a", "call_b"], "one ToolMessage per tool call, with matching ids"
    assert "18" in tool_msgs[0].content and "108.00" in tool_msgs[1].content, tool_msgs
    assert len(llm.received) == 2, "run ALL the requested tools before calling the model again"
    assert answer.startswith("18°C")


@checker.check("run_tool_loop() turns a tool exception into an error ToolMessage")
def _():
    llm = fake_chat_model(tool_call("convert_currency", {"amount": 1, "from_currency": "XXX", "to_currency": "USD"}), "Sorry.")
    _, messages = mod.run_tool_loop(llm, "convert")
    tool_msgs = [m for m in messages if isinstance(m, ToolMessage)]
    assert tool_msgs and "rror" in tool_msgs[0].content, tool_msgs


@checker.check("build_agent() answers a currency question with a tool  [live API]")
def _():
    result = mod.build_agent(get_chat_model(temperature=0)).invoke(
        {"messages": [("user", "Convert 100 EUR to USD.")]})
    assert any(isinstance(m, ToolMessage) for m in result["messages"]), "no tool was called"
    assert "108" in result["messages"][-1].text, result["messages"][-1].text


checker.run()
