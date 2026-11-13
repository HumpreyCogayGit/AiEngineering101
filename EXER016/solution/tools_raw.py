"""EXER016 — Tool Calling by Hand (reference solution).

The model never runs code. It can only ASK us to call a tool by returning a
`tool_calls` message. We run the function, send the result back as a `tool`
message, and call the model again — until it answers with plain text.
"""

from __future__ import annotations

import ast
import json
import operator

from aicourse.llm import get_llm_client
from aicourse.settings import get_settings

# --------------------------------------------------------------- the tools
FAKE_WEATHER = {
    "manila": {"temp_c": 31, "condition": "humid, scattered thunderstorms"},
    "tokyo": {"temp_c": 18, "condition": "clear"},
    "london": {"temp_c": 11, "condition": "light rain"},
    "nairobi": {"temp_c": 24, "condition": "sunny"},
}


def get_weather(city: str) -> dict:
    """Pretend weather service (a real one would call an HTTP API)."""
    data = FAKE_WEATHER.get(city.strip().lower())
    if data is None:
        return {"error": f"no weather data for {city}"}
    return {"city": city, **data}


_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def calculate(expression: str) -> float:
    """Safely evaluate arithmetic. NEVER use eval() on model output."""

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](_eval(node.operand))
        raise ValueError(f"unsupported expression: {ast.dump(node)[:60]}")

    return _eval(ast.parse(expression, mode="eval"))


# ------------------------------------------------- tool schemas for the model
TOOLS = [
    {
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
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate an arithmetic expression exactly. Use for any math.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "e.g. (12.5 * 4) / 3"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    },
]

REGISTRY = {"get_weather": get_weather, "calculate": calculate}


def run_tool(name: str, arguments_json: str) -> str:
    """Execute a requested tool. Errors are RETURNED to the model, not raised."""
    if name not in REGISTRY:
        return json.dumps({"error": f"unknown tool {name}"})
    try:
        args = json.loads(arguments_json or "{}")
        result = REGISTRY[name](**args)
        return json.dumps(result)
    except Exception as exc:  # the model can read the error and try again
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})


def run_conversation(client, user_text: str, max_rounds: int = 5, verbose: bool = False) -> str:
    messages: list[dict] = [
        {"role": "system", "content": "You are a helpful assistant. Use tools when they help."},
        {"role": "user", "content": user_text},
    ]
    for _ in range(max_rounds):
        response = client.chat.completions.create(
            model=get_settings().chat_model,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content or ""

        # 1. keep the assistant's tool request in the history
        messages.append(message.model_dump(exclude_none=True))
        # 2. run every requested tool and reply with a matching tool_call_id
        for call in message.tool_calls:
            result = run_tool(call.function.name, call.function.arguments)
            if verbose:
                print(f"  -> {call.function.name}({call.function.arguments}) = {result}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return "Sorry, I could not finish within the allowed number of steps."


def main() -> None:
    client = get_llm_client()
    for question in [
        "What's the weather in Tokyo?",
        "What is 1234 * 5678 + 42?",
        "Is it warmer in Manila or London right now, and by how many degrees?",
        "Tell me a fun fact about otters.",
    ]:
        print(f"\nQ: {question}")
        print("A:", run_conversation(client, question, verbose=True))


if __name__ == "__main__":
    main()
