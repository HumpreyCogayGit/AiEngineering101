"""EXER016 stretch goal 2 — run the tool calls of one round concurrently (EXER011).

    uv run python EXER016/stretch/goal2_concurrent_tools.py

When a model asks for three tools in one reply, the calls are independent,
so they can run at the same time. Real tools wait on a network; the weather
tool here sleeps for a second to stand in for that.

Two rules survive the change: every call still gets its own tool message
with the matching id, and the messages go back in the order they were asked.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from aicourse.llm import get_llm_client
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "tools_raw.py")

_real_weather = base.get_weather


def slow_weather(city: str) -> dict:
    time.sleep(1.0)  # a pretend network call
    return _real_weather(city)


base.REGISTRY["get_weather"] = slow_weather


def run_tools(tool_calls, concurrent: bool) -> list[dict]:
    """Run every requested tool; return the tool messages in request order."""
    def run(call) -> dict:
        return {"role": "tool", "tool_call_id": call.id,
                "content": base.run_tool(call.function.name, call.function.arguments)}

    if not concurrent:
        return [run(call) for call in tool_calls]
    # Threads suit tools that wait (I/O). map() returns results in input order.
    with ThreadPoolExecutor(max_workers=min(8, len(tool_calls))) as pool:
        return list(pool.map(run, tool_calls))


def run_conversation(client, user_text: str, concurrent: bool, max_rounds: int = 5) -> tuple[str, float]:
    """The exercise's loop. Returns (answer, seconds spent inside tools)."""
    messages: list[dict] = [
        {"role": "system", "content": "You are a helpful assistant. Use tools when they help. "
                                      "Request all the tool calls you need in one reply."},
        {"role": "user", "content": user_text},
    ]
    tool_seconds = 0.0
    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=get_settings().chat_model, messages=messages, tools=base.TOOLS
        )
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content or "", tool_seconds
        messages.append(message.model_dump(exclude_none=True))
        start = time.perf_counter()
        results = run_tools(message.tool_calls, concurrent)
        tool_seconds += time.perf_counter() - start
        print(f"  round with {len(results)} tool call(s): {time.perf_counter() - start:.1f}s in tools")
        messages.extend(results)
    return "Sorry, I could not finish within the allowed number of steps.", tool_seconds


def main() -> None:
    client = get_llm_client()
    question = "Compare the weather in Manila, Tokyo, London and Nairobi. Which is warmest?"
    timings = {}
    for label, concurrent in (("one after another", False), ("concurrently", True)):
        print(f"\n{label}:")
        answer, timings[label] = run_conversation(client, question, concurrent)
        print("A:", answer[:160])
    print(f"\nTime in tools: {timings['one after another']:.1f}s one after another, "
          f"{timings['concurrently']:.1f}s concurrently")


if __name__ == "__main__":
    main()
