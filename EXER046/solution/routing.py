"""EXER046 — Model Selection and Routing (reference solution).

    uv run python EXER046/solution/routing.py compare        # run the task suite on every candidate (live)
    uv run python EXER046/solution/routing.py route          # the helpdesk with a router and a fallback (live)

    AICOURSE_COMPARE_MODELS="gemma4:e4b,qwen2.5:3b"          # candidates on your provider (Ollama example)
    AICOURSE_COMPARE_MODELS="my-deployment@low,my-deployment@high"   # one model, two reasoning efforts

"Which model?" is an engineering question with measurable answers. For each
candidate, measure what the application needs: quality per task (classification,
structured output, choosing the right tool), latency, and cost. Then:

1. CHOOSE the cheapest candidate that meets every bar, not the "best" model.
2. ROUTE: easy questions to a cheap model, hard ones to a strong model, with
   rules you can read. Escalate when the cheap answer shows a quality problem.
3. FALL BACK to another model when the provider fails, for provider errors only.
4. WATCH RETIREMENTS: hosted models are withdrawn on a schedule. The same suite,
   re-run on the replacement, is how you know it is safe to switch.
"""

from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Literal

import openai
from langchain_core.tools import tool
from pydantic import BaseModel

HERE = Path(__file__).resolve().parent.parent
REGISTRY = HERE / "models.json"
TICKETS = HERE.parent / "EXER008" / "tickets.json"
PROVIDER_ERRORS = (openai.APIConnectionError, openai.APITimeoutError, openai.RateLimitError,
                   openai.InternalServerError)


# ------------------------------------------------------------------ candidates and the registry (given)
@dataclass(frozen=True)
class Candidate:
    name: str                       # how it is shown: "gemma4:e4b" or "my-deployment@low"
    model: str
    reasoning_effort: str | None = None

    def chat_model(self, **kwargs):
        from aicourse.llm import get_chat_model

        if self.reasoning_effort:
            kwargs["reasoning_effort"] = self.reasoning_effort
        return get_chat_model(model=self.model, **kwargs)


def parse_candidates(spec: str) -> list[Candidate]:
    """"a,b@low" -> [Candidate("a", "a"), Candidate("b@low", "b", "low")]."""
    out = []
    for part in (p.strip() for p in spec.split(",") if p.strip()):
        model, _, effort = part.partition("@")
        out.append(Candidate(part, model, effort or None))
    return out


def load_registry(path: Path = REGISTRY) -> dict[str, dict]:
    """Known models: price per million input / output tokens, and a retirement date if announced."""
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


# ------------------------------------------------------------------ the task suite (given)
class Order(BaseModel):
    product: str
    quantity: int


@tool
def search_knowledge_base(query: str) -> str:
    """Search Nimbus Coffee's documents: products, prices, policies, shipping, stores, HR."""
    return "(not run in the suite)"


@tool
def calculator(expression: str) -> str:
    """Evaluate arithmetic exactly, e.g. '3 * 390 + 250'."""
    return "(not run in the suite)"


@tool
def notes_add_note(title: str, content: str) -> str:
    """Save a note for the user."""
    return "(not run in the suite)"


EXTRACT_CASES = [
    ("Please send me three bags of Barako Bold.", Order(product="Barako Bold", quantity=3)),
    ("I'd like 2 x Decaf Cloud, thanks", Order(product="Decaf Cloud", quantity=2)),
    ("One Hand Grinder Pro for the office please", Order(product="Hand Grinder Pro", quantity=1)),
    ("Can I get twelve Benguet Highlands?", Order(product="Benguet Highlands", quantity=12)),
]
TOOL_CASES = [
    ("What is your refund policy for opened bags?", "search_knowledge_base"),
    ("What is 3 * 390 + 3450?", "calculator"),
    ("Save a note titled 'Supplier' saying call Benguet on Friday.", "notes_add_note"),
    ("Do you ship to Japan?", "search_knowledge_base"),
]


def suite(limit_tickets: int = 8) -> list[dict]:
    tickets = json.loads(TICKETS.read_text(encoding="utf-8"))[:limit_tickets]
    return ([{"task": "classify", "input": t["text"], "expected": t["label"]} for t in tickets]
            + [{"task": "extract", "input": text, "expected": order.model_dump()} for text, order in EXTRACT_CASES]
            + [{"task": "tool", "input": text, "expected": name} for text, name in TOOL_CASES])


def run_case(llm, case: dict) -> dict:
    """One case on one model: did it get it right, how long did it take, how many tokens."""
    start = time.perf_counter()
    usage = {}
    try:
        if case["task"] == "classify":
            msg = llm.invoke([("system", "Classify the support ticket as billing, technical, account or other. "
                                         "Reply with the label only, lowercase."), ("user", case["input"])])
            output, usage = msg.text.strip().lower().strip("."), msg.usage_metadata or {}
        elif case["task"] == "extract":
            result = llm.with_structured_output(Order, include_raw=True).invoke(
                [("system", "Extract the product name and the quantity as a number."), ("user", case["input"])])
            parsed = result["parsed"]
            output, usage = (parsed.model_dump() if parsed else None), result["raw"].usage_metadata or {}
        else:
            msg = llm.bind_tools([search_knowledge_base, calculator, notes_add_note]).invoke(
                [("system", "You are the Nimbus helpdesk. Use the right tool."), ("user", case["input"])])
            output, usage = (msg.tool_calls[0]["name"] if msg.tool_calls else None), msg.usage_metadata or {}
        error = None
    except Exception as exc:  # a failure is a result: count it, do not stop the suite
        output, error = None, f"{type(exc).__name__}: {exc}"[:120]
    return {"task": case["task"], "correct": output == case["expected"], "output": output, "error": error,
            "seconds": time.perf_counter() - start,
            "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0)}


# ------------------------------------------------------------------ 1. measure and choose
def summarize(rows: list[dict], price: dict | None) -> dict:
    """One candidate's results: accuracy per task, latency, and cost per 1,000 requests."""
    tasks = sorted({r["task"] for r in rows})
    seconds = sorted(r["seconds"] for r in rows)
    p95 = seconds[max(0, -(-95 * len(seconds) // 100) - 1)]
    cost = None
    if price:
        per_request = statistics.mean(r["input_tokens"] * price["input"] + r["output_tokens"] * price["output"]
                                      for r in rows) / 1_000_000
        cost = round(per_request * 1000, 4)
    return {"accuracy": {t: round(statistics.mean(r["correct"] for r in rows if r["task"] == t), 3) for t in tasks},
            "errors": sum(r["error"] is not None for r in rows),
            "p50_seconds": round(statistics.median(seconds), 2), "p95_seconds": round(p95, 2),
            "cost_per_1000": cost}


def choose(summaries: dict[str, dict], min_accuracy: dict[str, float], max_p95: float) -> str | None:
    """The cheapest candidate that meets every accuracy bar and the latency bar (ties: the faster one).

    A candidate with an unknown price can only be chosen if no priced candidate qualifies.
    """
    qualified = [name for name, s in summaries.items()
                 if all(s["accuracy"].get(task, 0) >= bar for task, bar in min_accuracy.items())
                 and s["p95_seconds"] <= max_p95]
    if not qualified:
        return None
    return min(qualified, key=lambda n: (summaries[n]["cost_per_1000"] is None,
                                         summaries[n]["cost_per_1000"] or 0, summaries[n]["p95_seconds"]))


# ------------------------------------------------------------------ 2. route and escalate
HARD_WORDS = ("total", "calculate", "compare", "difference", "why", "explain", "complaint", "broken", "damaged")
HEDGES = ("don't know", "do not know", "not sure", "cannot find", "can't find", "unable to")


def route_question(question: str) -> Literal["small", "large"]:
    """Readable rules, not a model: a router you cannot explain is a second problem."""
    text = question.lower()
    if len(text.split()) > 25 or text.count("?") > 1:
        return "large"  # long or several questions in one
    if any(re.search(rf"\b{w}\b", text) for w in HARD_WORDS):
        return "large"  # arithmetic, comparisons, reasons, complaints
    return "small"


def needs_escalation(reply: dict) -> list[str]:
    """Quality signals in the small model's reply that justify asking the large one. [] = keep it."""
    reasons = []
    answer = reply.get("answer", "").lower().replace("’", "'")
    if not answer.strip():
        reasons.append("empty answer")
    if any(h in answer for h in HEDGES) and "search_knowledge_base" in reply.get("tools_used", []):
        reasons.append("searched the documents and still could not answer")
    if reply.get("error"):
        reasons.append("the call failed")
    return reasons


@dataclass
class RoutedHelpdesk:
    """small(question, thread) and large(question, thread) return the capstone Reply as a dict (given)."""
    small: Callable[[str, str], dict]
    large: Callable[[str, str], dict]
    log: list[dict] = field(default_factory=list)

    def ask(self, question: str, thread_id: str) -> dict:
        route = route_question(question)
        reply = (self.small if route == "small" else self.large)(question, thread_id)
        reasons = needs_escalation(reply) if route == "small" else []
        if reasons:
            reply = self.large(question, thread_id)
        self.log.append({"question": question, "route": route, "escalated": bool(reasons), "reasons": reasons})
        return {**reply, "route": "small→large" if reasons else route}


# ------------------------------------------------------------------ 3. fall back on provider errors
def with_provider_fallback(primary, fallback):
    """The primary model, or the fallback when the provider fails. Only for provider errors:
    a bug in your request fails on every model and must not be hidden."""
    return primary.with_fallbacks([fallback], exceptions_to_handle=PROVIDER_ERRORS)


# ------------------------------------------------------------------ 4. retirements
def retiring_soon(registry: dict[str, dict], today: date, within_days: int = 90) -> list[tuple[str, int]]:
    """[(model, days left)] for models retiring within `within_days`, soonest first. Past dates count too."""
    out = []
    for name, info in registry.items():
        if info.get("retires"):
            left = (date.fromisoformat(info["retires"]) - today).days
            if left <= within_days:
                out.append((name, left))
    return sorted(out, key=lambda item: item[1])


# ------------------------------------------------------------------ demo (given)
def candidates_from_env() -> list[Candidate]:
    from aicourse.settings import get_settings

    return parse_candidates(os.environ.get("AICOURSE_COMPARE_MODELS") or get_settings().chat_model)


def compare() -> None:
    registry, cases = load_registry(), suite()
    summaries = {}
    for candidate in candidates_from_env():
        llm = candidate.chat_model(temperature=0)
        rows = [run_case(llm, case) for case in cases]
        summaries[candidate.name] = summarize(rows, registry.get(candidate.model, {}).get("price"))
        s = summaries[candidate.name]
        cost = "unknown" if s["cost_per_1000"] is None else f"${s['cost_per_1000']:.4f}"
        print(f"{candidate.name:<24} {json.dumps(s['accuracy'])}  p50 {s['p50_seconds']} s  p95 {s['p95_seconds']} s  "
              f"errors {s['errors']}  cost/1000 {cost}")
    bars = {"classify": 0.75, "extract": 1.0, "tool": 1.0}
    print(f"\nBars: {bars}, p95 <= 8 s  ->  choose: {choose(summaries, bars, max_p95=8.0)}")
    for name, left in retiring_soon(registry, date.today()):
        print(f"WARNING: {name} retires in {left} days: run this suite on its replacement now.")


def route_demo() -> None:
    import asyncio
    import tempfile
    from dataclasses import asdict

    from aicourse.stretch import solution_path

    solution_path(str(HERE.parent / "EXER037" / "solution" / "x.py"))
    import assistant as capstone
    import tools as capstone_tools

    candidates = candidates_from_env()
    small_c, large_c = candidates[0], candidates[-1]
    loop = asyncio.new_event_loop()

    async def build(c: Candidate, notes: Path):
        tools = capstone_tools.LOCAL_TOOLS + await capstone_tools.load_mcp_tools(notes)
        return await capstone.Assistant(llm=c.chat_model(temperature=0), tools=tools).setup()

    with tempfile.TemporaryDirectory() as tmp:
        small = loop.run_until_complete(build(small_c, Path(tmp) / "a.json"))
        large = loop.run_until_complete(build(large_c, Path(tmp) / "b.json"))
        helpdesk = RoutedHelpdesk(lambda q, t: asdict(loop.run_until_complete(small.ask(q, t))),
                                  lambda q, t: asdict(loop.run_until_complete(large.ask(q, t))))
        for i, q in enumerate(["Is shipping free?", "Do you deliver to Japan?",
                               "What do 3 bags of Barako Bold and a Hand Grinder Pro cost in total?",
                               "Who is the CEO of Nimbus?"]):
            reply = helpdesk.ask(q, f"t{i}")
            answer = " ".join(reply["answer"].split())
            print(f"{reply['route']:<12} {reply['tokens']:>5} tokens  {q}\n             {answer[:100]}")
    print(f"\nsmall = {small_c.name}, large = {large_c.name}")


if __name__ == "__main__":
    {"compare": compare, "route": route_demo}.get(sys.argv[1] if len(sys.argv) > 1 else "compare", compare)()
