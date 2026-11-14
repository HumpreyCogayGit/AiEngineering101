"""EXER035 — Observability and Cost.

You can't improve (or afford) what you can't see. LangChain emits CALLBACK
events for every model call and tool call: start, end, error, with run ids
that link children to parents. A callback handler turns them into:
  - a TRACE   (what happened, in what order)
  - METRICS   (latency, tokens, cost, errors)

Hosted tracing (LangSmith) does this for you: set LANGSMITH_TRACING=true and
LANGSMITH_API_KEY in .env — no code changes. Here we build it ourselves.

    uv run python EXER035/starter/observability.py
    uv run python EXER035/check.py
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.tools import tool

from aicourse.llm import get_chat_model
from aicourse.rag import format_docs, get_vector_store

# USD per 1M tokens. Example values — check your provider's pricing page. A local model costs nothing per token.
PRICES = {"input": 0.40, "output": 1.60}


@dataclass
class Span:
    kind: str                 # "llm" or "tool"
    name: str
    run_id: UUID
    parent_run_id: UUID | None
    start: float
    end: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
    detail: str = ""

    @property
    def duration(self) -> float:
        return (self.end or time.perf_counter()) - self.start


# eq=False keeps the handler hashable: LangChain puts handlers in a set when it merges the
# callbacks of nested runs (a graph inside a graph), and a plain dataclass is not hashable.
@dataclass(eq=False)
class UsageTracker(BaseCallbackHandler):
    """One Span per model call and per tool call, keyed by run_id."""

    spans: dict[UUID, Span] = field(default_factory=dict)

    # ------------------------------------------------------------ model events
    def on_chat_model_start(self, serialized: dict, messages: list, *, run_id: UUID,
                            parent_run_id: UUID | None = None, **kwargs: Any) -> None:
        name = (kwargs.get("metadata") or {}).get("ls_model_name") or serialized.get("name", "chat_model")
        self.spans[run_id] = Span("llm", name, run_id, parent_run_id, time.perf_counter())

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        """Close the span and record token usage.

        - span = self.spans.get(run_id); return if None; span.end = time.perf_counter()
        - message = response.generations[0][0].message   (use getattr(..., "message", None))
        - usage = message.usage_metadata or {}  → span.input_tokens / span.output_tokens
                  (keys "input_tokens" and "output_tokens", default 0)
        - span.detail = "→ calls <tool names>" if message.tool_calls else "→ answer"
        """
        # TODO
        raise NotImplementedError("on_llm_end")

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        if run_id in self.spans:
            self.spans[run_id].end = time.perf_counter()
            self.spans[run_id].error = f"{type(error).__name__}: {error}"

    # ------------------------------------------------------------ tool events
    def on_tool_start(self, serialized: dict, input_str: str, *, run_id: UUID,
                      parent_run_id: UUID | None = None, **kwargs: Any) -> None:
        """Create a Span("tool", serialized.get("name", "tool"), run_id, parent_run_id,
        time.perf_counter(), detail=input_str[:60])."""
        # TODO
        raise NotImplementedError("on_tool_start")

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        # TODO: set the span's end time
        raise NotImplementedError("on_tool_end")

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        # TODO: set the span's end time AND its error: f"{type(error).__name__}: {error}"
        raise NotImplementedError("on_tool_error")

    # ------------------------------------------------------------ reporting
    def report(self, prices: dict[str, float] = PRICES) -> dict:
        """Totals over all spans:
        {"llm_calls", "tool_calls", "errors", "input_tokens", "output_tokens",
         "cost_usd" (per-million pricing!), "llm_seconds", "tool_seconds" (rounded to 3 decimals)}"""
        # TODO
        raise NotImplementedError("report")

    def timeline(self) -> list[str]:
        """One line per span in start order: tool spans tagged, durations and tokens shown."""
        lines = []
        for s in sorted(self.spans.values(), key=lambda s: s.start):
            if s.kind == "llm":
                line = f"LLM  {s.name:<22} {s.duration:6.2f}s  in={s.input_tokens:<5} out={s.output_tokens:<4} {s.detail}"
            else:
                line = f"TOOL {s.name:<22} {s.duration:6.2f}s  {s.detail}"
            if s.error:
                line += f"  ❌ {s.error}"
            lines.append(line)
        return lines


# ------------------------------------------------------------------ an agent to observe
@tool
def search_kb(query: str) -> str:
    """Search the Nimbus Coffee knowledge base."""
    return format_docs(get_vector_store().similarity_search(query, k=3))


@tool
def flaky_inventory(product: str) -> str:
    """Check stock for a product (this service is unreliable)."""
    raise ConnectionError("inventory service timed out")


def build_agent():
    return create_agent(get_chat_model(temperature=0), [search_kb, flaky_inventory],
                        system_prompt="Answer questions about Nimbus Coffee using the tools.")


def main() -> None:
    tracker = UsageTracker()
    agent = build_agent()
    for q in ["What is the refund window for unopened beans, and is shipping free?",
              "Is Barako Bold in stock?"]:
        try:
            result = agent.invoke({"messages": [("user", q)]}, {"callbacks": [tracker]})
            print(f"\nQ: {q}\nA: {result['messages'][-1].text[:200]}")
        except Exception as exc:  # the tracker still recorded everything up to the failure
            print(f"\nQ: {q}\nRun FAILED: {type(exc).__name__}: {exc}  (see the timeline below)")
    print("\nTimeline:")
    for line in tracker.timeline():
        print("  ", line)
    print("\nReport:", tracker.report())


if __name__ == "__main__":
    main()
