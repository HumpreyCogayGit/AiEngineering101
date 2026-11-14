"""EXER017 stretch goal 1 — `parallel_tool_calls=False`, and what it does to the trace.

    uv run python EXER017/stretch/goal1_no_parallel_calls.py

The same question, answered twice. With parallel tool calls the model asks
for both tools in ONE reply. With the feature off it asks for one tool per
turn, so the trace gets longer: more model calls, more latency, more tokens.
You pay that when a call must see the result of the one before it.

(The setting is a request to the provider. Some local models ignore it.)
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "lc_tools.py")


def run_tool_loop(llm, question: str, parallel: bool, max_rounds: int = 6) -> list[BaseMessage]:
    """The exercise's loop, with the parallel-calls switch exposed."""
    by_name = {t.name: t for t in base.TOOLS}
    llm_with_tools = llm.bind_tools(base.TOOLS, parallel_tool_calls=parallel)
    messages: list[BaseMessage] = [
        SystemMessage(content="You are a helpful assistant. Use tools when they help."),
        HumanMessage(content=question),
    ]
    for _ in range(max_rounds):
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)
        if not ai_msg.tool_calls:
            break
        for call in ai_msg.tool_calls:
            try:
                messages.append(by_name[call["name"]].invoke(call))
            except Exception as exc:
                messages.append(ToolMessage(content=f"Error: {exc}", tool_call_id=call["id"], status="error"))
    return messages


def print_trace(messages: list[BaseMessage]) -> None:
    for m in messages:
        calls = getattr(m, "tool_calls", None)
        extra = f" tool_calls={[c['name'] for c in calls]}" if calls else ""
        print(f"  {type(m).__name__:<14}{extra} {m.text[:60]!r}")
    model_calls = sum(type(m).__name__ == "AIMessage" for m in messages)
    print(f"  => {model_calls} model calls, {len(messages)} messages")


def main() -> None:
    llm = get_chat_model(temperature=0)
    question = "How much is 2500 PHP in EUR, and what's the weather in Tokyo?"
    for parallel in (True, False):
        print(f"\nparallel_tool_calls={parallel}")
        print_trace(run_tool_loop(llm, question, parallel))


if __name__ == "__main__":
    main()
