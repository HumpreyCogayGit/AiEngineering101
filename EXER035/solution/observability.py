"""EXER035 — Observability and Cost (reference solution).

You can't improve (or afford) what you can't see. LangChain emits CALLBACK
events for every model call and tool call: start, end, error, with run ids
that link children to parents. A callback handler turns them into:
  - a TRACE   (what happened, in what order, nested)
  - METRICS   (latency, tokens, cost, errors)

Hosted tracing (LangSmith) does this for you: set LANGSMITH_TRACING=true and
LANGSMITH_API_KEY in .env — no code changes. Here we build it ourselves.
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


@dataclass
class UsageTracker(BaseCallbackHandler):
    spans: dict[UUID, Span] = field(default_factory=dict)

    # ------------------------------------------------------------ model events
    def on_chat_model_start(self, serialized: dict, messages: list, *, run_id: UUID,
                            parent_run_id: UUID | None = None, **kwargs: Any) -> None:
        name = (kwargs.get("metadata") or {}).get("ls_model_name") or serialized.get("name", "chat_model")
        self.spans[run_id] = Span("llm", name, run_id, parent_run_id, time.perf_counter())

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, **kwargs: Any) -> None:
        span = self.spans.get(run_id)
        if span is None:
            return
        span.end = time.perf_counter()
        message = getattr(response.generations[0][0], "message", None)
        usage = getattr(message, "usage_metadata", None) or {}
        span.input_tokens = usage.get("input_tokens", 0)
        span.output_tokens = usage.get("output_tokens", 0)
        calls = getattr(message, "tool_calls", None) or []
        span.detail = f"→ calls {', '.join(c['name'] for c in calls)}" if calls else "→ answer"

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        if run_id in self.spans:
            self.spans[run_id].end = time.perf_counter()
            self.spans[run_id].error = f"{type(error).__name__}: {error}"

    # ------------------------------------------------------------ tool events
    def on_tool_start(self, serialized: dict, input_str: str, *, run_id: UUID,
                      parent_run_id: UUID | None = None, **kwargs: Any) -> None:
        self.spans[run_id] = Span("tool", serialized.get("name", "tool"), run_id, parent_run_id,
                                  time.perf_counter(), detail=input_str[:60])

    def on_tool_end(self, output: Any, *, run_id: UUID, **kwargs: Any) -> None:
        if run_id in self.spans:
            self.spans[run_id].end = time.perf_counter()

    def on_tool_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        if run_id in self.spans:
            self.spans[run_id].end = time.perf_counter()
            self.spans[run_id].error = f"{type(error).__name__}: {error}"

    # ------------------------------------------------------------ reporting
    def report(self, prices: dict[str, float] = PRICES) -> dict:
        llm = [s for s in self.spans.values() if s.kind == "llm"]
        tools = [s for s in self.spans.values() if s.kind == "tool"]
        input_tokens = sum(s.input_tokens for s in llm)
        output_tokens = sum(s.output_tokens for s in llm)
        return {
            "llm_calls": len(llm),
            "tool_calls": len(tools),
            "errors": sum(1 for s in self.spans.values() if s.error),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": input_tokens * prices["input"] / 1e6 + output_tokens * prices["output"] / 1e6,
            "llm_seconds": round(sum(s.duration for s in llm), 3),
            "tool_seconds": round(sum(s.duration for s in tools), 3),
        }

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
