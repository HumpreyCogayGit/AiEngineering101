"""EXER027 stretch goal 2 — stream the agent's tokens as well as its steps (EXER007).

    uv run python EXER027/stretch/goal2_stream_tokens.py

`stream_mode="updates"` (the exercise) yields one item per finished NODE.
`stream_mode="messages"` yields the model's output token by token, from
inside the node. Asking for both gives (mode, data) pairs, so one loop can
show the steps as they complete and the final answer as it is written.
"""

from __future__ import annotations

from langchain_core.messages import AIMessageChunk

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "react_agent.py")


def stream_run(graph, question: str) -> dict:
    """Print steps and tokens as they happen. Returns counts, for the summary line."""
    counts = {"tokens": 0, "steps": 0}
    writing = False
    for mode, data in graph.stream({"messages": [("user", question)]}, stream_mode=["updates", "messages"]):
        if mode == "messages":
            chunk, metadata = data
            # Only the model's text: tool results also pass through this mode.
            if isinstance(chunk, AIMessageChunk) and chunk.text and metadata.get("langgraph_node") == "agent":
                if not writing:
                    print("[agent] ", end="")
                    writing = True
                print(chunk.text, end="", flush=True)
                counts["tokens"] += 1
        else:  # "updates": a node finished
            for node, update in data.items():
                counts["steps"] += 1
                for message in update["messages"]:
                    calls = [f"{c['name']}({c['args']})" for c in getattr(message, "tool_calls", [])]
                    if calls:
                        print(f"[{node}] calls {', '.join(calls)}")
                    elif node == "tools":
                        print(f"[tools] {message.text[:80]}")
            if writing:
                print()
                writing = False
    return counts


def main() -> None:
    graph = base.build_agent(get_chat_model(temperature=0))
    question = "I want 3 bags of Barako Bold and 2 of Mount Apo Sunrise. What's the total in pesos?"
    print(f"Q: {question}\n")
    counts = stream_run(graph, question)
    print(f"\n{counts['steps']} node steps, {counts['tokens']} streamed text chunks")


if __name__ == "__main__":
    main()
