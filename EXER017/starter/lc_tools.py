"""EXER017 — Tools in LangChain.

@tool turns a typed, documented Python function into a tool: the name,
description and JSON schema are generated from the signature and docstring.
`llm.bind_tools(tools)` sends those schemas with every call.

    uv run python EXER017/starter/lc_tools.py
    uv run python EXER017/check.py
"""

from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from aicourse.llm import get_chat_model

RATES_TO_USD = {"USD": 1.0, "EUR": 1.08, "PHP": 0.0175, "JPY": 0.0067, "GBP": 1.27}
FAKE_WEATHER = {"manila": 31, "tokyo": 18, "london": 11, "nairobi": 24}


@tool
def get_weather(city: str) -> str:
    """Get the current temperature in Celsius for a city."""
    temp = FAKE_WEATHER.get(city.strip().lower())
    return f"{city}: {temp}°C" if temp is not None else f"No data for {city}"


# TODO: decorate with @tool, add type hints and a docstring (the docstring becomes
#       the description the model reads!). Convert using RATES_TO_USD:
#           value = amount * RATES_TO_USD[src] / RATES_TO_USD[dst]
#       Return e.g. "2500 PHP = 40.51 EUR". Raise ValueError for unknown currencies.
def convert_currency(amount, from_currency, to_currency):
    raise NotImplementedError("convert_currency")


# TODO: a @tool `word_count(text: str) -> int` that counts the words in a text.


TOOLS = [get_weather]  # TODO: add convert_currency and word_count


def run_tool_loop(llm: BaseChatModel, question: str, max_rounds: int = 5) -> tuple[str, list[BaseMessage]]:
    """The EXER016 loop, with LangChain doing the message bookkeeping.

    by_name = {t.name: t for t in TOOLS}
    llm_with_tools = llm.bind_tools(TOOLS)
    messages = [SystemMessage(...), HumanMessage(question)]
    repeat up to max_rounds:
        ai_msg = llm_with_tools.invoke(messages); messages.append(ai_msg)
        if not ai_msg.tool_calls: return ai_msg.text, messages
        for call in ai_msg.tool_calls:          # call = {"name", "args", "id"}
            # One AIMessage can request SEVERAL tools (parallel tool calls). Answer every
            # one with its own ToolMessage before you call the model again.
            - unknown tool -> append ToolMessage(content="Unknown tool ...", tool_call_id=call["id"])
            - else try: messages.append(by_name[call["name"]].invoke(call))
                  (invoking a tool with the whole tool call returns a ready ToolMessage)
              except Exception as exc:
                  append ToolMessage(content=f"Error: {exc}", tool_call_id=call["id"], status="error")
    return "Stopped: too many tool rounds.", messages
    """
    # TODO
    raise NotImplementedError("run_tool_loop")


def build_agent(llm: BaseChatModel):
    """The same loop, prebuilt: create_agent(llm, TOOLS, system_prompt=...)."""
    # TODO
    raise NotImplementedError("build_agent")


def main() -> None:
    print("Tool schema generated from the function:")
    print(" ", convert_currency.name, "-", convert_currency.description)
    print(" ", convert_currency.args)

    llm = get_chat_model(temperature=0)
    question = "How much is 2500 PHP in EUR, and what's the weather in Tokyo?"
    answer, messages = run_tool_loop(llm, question)
    print(f"\nQ: {question}\nA: {answer}")
    print("\nMessage trace:")
    for m in messages:
        extra = f" tool_calls={[c['name'] for c in m.tool_calls]}" if getattr(m, "tool_calls", None) else ""
        print(f"  {type(m).__name__:<14}{extra} {m.text[:70]!r}")

    print("\nSame question via create_agent:")
    result = build_agent(llm).invoke({"messages": [("user", question)]})
    print("A:", result["messages"][-1].text)


if __name__ == "__main__":
    main()
