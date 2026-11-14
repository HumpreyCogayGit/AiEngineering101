"""EXER007 stretch goal 2 — stream tool-call deltas and assemble the arguments.

    uv run python EXER007/stretch/goal2_tool_call_deltas.py

This prepares EXER016. When a model asks for a tool while streaming, the
request arrives in pieces, like text does:

    delta.tool_calls[0]  id="call_1", function.name="get_weather", function.arguments=""
    delta.tool_calls[0]  function.arguments='{"ci'
    delta.tool_calls[0]  function.arguments='ty": "Tokyo"}'

The id and name come once; `arguments` is a JSON string that arrives in
fragments. `index` says which call a fragment belongs to, because a model can
request several tools in one reply.
"""

from __future__ import annotations

import json

from aicourse.llm import get_llm_client
from aicourse.settings import get_settings

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name, e.g. Tokyo"}},
            "required": ["city"],
            "additionalProperties": False,
        },
    },
}


def assemble_tool_calls(stream, on_fragment=None) -> tuple[str, list[dict]]:
    """Consume a stream. Returns (text, [{"id", "name", "arguments": dict}, ...])."""
    text: list[str] = []
    calls: dict[int, dict] = {}  # index -> the call being assembled
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            text.append(delta.content)
        for part in delta.tool_calls or []:
            call = calls.setdefault(part.index, {"id": "", "name": "", "arguments": ""})
            if part.id:
                call["id"] = part.id
            if part.function and part.function.name:
                call["name"] = part.function.name
            if part.function and part.function.arguments:
                call["arguments"] += part.function.arguments
                if on_fragment:
                    on_fragment(part.index, part.function.arguments)
    # Only now, with every fragment joined, is `arguments` complete JSON.
    finished = [{**calls[i], "arguments": json.loads(calls[i]["arguments"] or "{}")} for i in sorted(calls)]
    return "".join(text), finished


def main() -> None:
    stream = get_llm_client().chat.completions.create(
        model=get_settings().chat_model,
        messages=[{"role": "user", "content": "What is the weather in Tokyo and in Manila?"}],
        tools=[WEATHER_TOOL],
        stream=True,
    )
    print("Fragments as they arrive:")
    text, calls = assemble_tool_calls(stream, lambda i, frag: print(f"  call {i}: {frag!r}"))
    print("\nAssembled tool calls:")
    for call in calls:
        print(f"  {call['id'][:12]:<12} {call['name']}({call['arguments']})")
    if text:
        print("Text:", text)


if __name__ == "__main__":
    main()
