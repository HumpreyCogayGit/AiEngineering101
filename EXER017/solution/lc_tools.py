"""EXER017 — Tools in LangChain (reference solution).

@tool turns a typed, documented Python function into a tool: the name,
description and JSON schema are generated from the signature and docstring.
`llm.bind_tools(tools)` sends those schemas with every call.
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


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount between currencies. Currencies are ISO codes like USD, EUR, PHP, JPY, GBP."""
    src, dst = from_currency.upper(), to_currency.upper()
    if src not in RATES_TO_USD or dst not in RATES_TO_USD:
        raise ValueError(f"Unsupported currency. Supported: {', '.join(RATES_TO_USD)}")
    value = amount * RATES_TO_USD[src] / RATES_TO_USD[dst]
    return f"{amount} {src} = {value:.2f} {dst}"


@tool
def word_count(text: str) -> int:
    """Count the words in a piece of text."""
    return len(text.split())


TOOLS = [get_weather, convert_currency, word_count]


def run_tool_loop(llm: BaseChatModel, question: str, max_rounds: int = 5) -> tuple[str, list[BaseMessage]]:
    """The EXER016 loop, with LangChain doing the message bookkeeping."""
    by_name = {t.name: t for t in TOOLS}
    llm_with_tools = llm.bind_tools(TOOLS)
    messages: list[BaseMessage] = [
        SystemMessage(content="You are a helpful assistant. Use tools when they help."),
        HumanMessage(content=question),
    ]
    for _ in range(max_rounds):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)
        if not ai_msg.tool_calls:
            return ai_msg.text, messages
        # One AIMessage can request several tools at once (parallel tool calls).
        # Every call needs its own ToolMessage, matched by id, before the next model call.
        for call in ai_msg.tool_calls:
            selected = by_name.get(call["name"])
            if selected is None:
                messages.append(ToolMessage(content=f"Unknown tool {call['name']}", tool_call_id=call["id"]))
                continue
            try:
                # Invoking a tool with the whole tool call returns a ready ToolMessage.
                messages.append(selected.invoke(call))
            except Exception as exc:
                messages.append(ToolMessage(content=f"Error: {exc}", tool_call_id=call["id"], status="error"))
    return "Stopped: too many tool rounds.", messages


def build_agent(llm: BaseChatModel):
    """The same loop, prebuilt: create_agent runs model -> tools -> model until done."""
    return create_agent(llm, TOOLS, system_prompt="You are a helpful assistant. Use tools when they help.")


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
