"""EXER016 stretch goal 1 — a `get_time(timezone)` tool, and a question that needs two tools.

    uv run python EXER016/stretch/goal1_time_tool.py

Adding a tool is three steps, and the loop does not change:
1. the function,
2. its JSON schema (what the model reads),
3. its entry in the registry (what your dispatcher runs).
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aicourse.llm import get_llm_client
from aicourse.stretch import solution_module

base = solution_module(__file__, "tools_raw.py")


def get_time(timezone: str) -> dict:
    """Current local time in an IANA timezone such as "Asia/Tokyo"."""
    try:
        now = datetime.now(ZoneInfo(timezone))
    except (ZoneInfoNotFoundError, ValueError):
        # An error the model can act on: it says what a valid value looks like.
        return {"error": f"unknown timezone {timezone!r}. Use an IANA name such as Asia/Manila or Europe/London."}
    return {"timezone": timezone, "time": now.strftime("%H:%M"), "date": now.strftime("%Y-%m-%d"),
            "weekday": now.strftime("%A")}


TIME_TOOL = {
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "Get the current local time and date in a timezone. Use for any question about what time it is.",
        "parameters": {
            "type": "object",
            "properties": {"timezone": {"type": "string",
                                        "description": "IANA timezone name, e.g. Asia/Tokyo or Europe/London"}},
            "required": ["timezone"],
            "additionalProperties": False,
        },
    },
}

# The loop in the solution reads these two module-level objects, so extending them is enough.
base.TOOLS.append(TIME_TOOL)
base.REGISTRY["get_time"] = get_time


def main() -> None:
    client = get_llm_client()
    print("Tools:", [t["function"]["name"] for t in base.TOOLS])
    for question in [
        "What time is it in Tokyo right now, and what's the weather there?",
        "How many hours until midnight in London? Use the tools for the time and for the arithmetic.",
        "What time is it in Atlantis?",
    ]:
        print(f"\nQ: {question}")
        print("A:", base.run_conversation(client, question, verbose=True))


if __name__ == "__main__":
    main()
