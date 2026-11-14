"""EXER040 — Context Engineering (starter).

Prompt engineering (EXER008) is about the wording of one prompt. Context
engineering is about EVERYTHING the model reads on a call, and the context
window is a budget you spend on purpose:

    system prompt + tool definitions + history + tool results + question

This exercise works through five parts of it:

    budgeting   how many tokens each section takes, and a hard budget
    tool output a 38 KB raw API response vs. a compact projection of it
    isolation   a sub-agent reads the raw response and returns only findings
    position    where a fact sits in a long context, and how much noise is around it
    measuring   accuracy AND tokens per call for every way of building the context
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import tiktoken
from langchain_core.language_models import BaseChatModel

from aicourse.llm import get_chat_model

HERE = Path(__file__).resolve().parent.parent
ACCOUNT = HERE / "account.json"  # the raw response of the order API, as it comes off the wire
CASES = HERE / "cases.json"      # probe questions, needle notes and distractor notes
ENCODING = tiktoken.get_encoding("o200k_base")

SYSTEM = ("You are the Nimbus Coffee wholesale support assistant. Answer the question about the customer's "
          "account from the material you are given. Be brief. If the material does not contain the answer, "
          "say you do not know.")

# The tool definitions the support agent is given. An API sends them with EVERY call,
# so they are input tokens like any other text, even when no tool is called.
TOOLS = [
    {"name": "get_account_orders", "description": "All orders of a wholesale account, newest last.",
     "parameters": {"type": "object", "properties": {"account_id": {"type": "string"}}, "required": ["account_id"]}},
    {"name": "search_knowledge_base", "description": "Search Nimbus Coffee policies, products and shipping rules.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
                    "required": ["query"]}},
    {"name": "create_ticket", "description": "Open a support ticket for the account.",
     "parameters": {"type": "object", "properties": {"account_id": {"type": "string"}, "summary": {"type": "string"},
                                                     "priority": {"enum": ["low", "normal", "high"]}},
                    "required": ["account_id", "summary"]}},
]

HISTORY = ("user: Hi, Marco from Bayani Café here. I have a few questions about our orders.\n"
           "assistant: Hello Marco! I've pulled up the Bayani Café account. What would you like to know?")

SUBAGENT_PROMPT = ("You read raw API data for another assistant. Extract only the facts needed to answer the "
                   "question below, in at most 60 words. Quote numbers and identifiers exactly. No advice.")

SECTION_ORDER = ["system", "tools", "history", "tool_result"]  # the order of the context, and its priority
CUT_MARKER = "\n[... cut to fit the budget]"

Sections = dict  # {"system": str, "tools": str, "history": str, "tool_result": str}
Builder = Callable[[str], tuple[Sections, int]]  # question -> (sections, tokens spent outside the main call)


# ------------------------------------------------------------------ 1. budgeting
def count_tokens(text: str) -> int:
    """Tokens of a piece of text: len(ENCODING.encode(text))."""
    # TODO
    raise NotImplementedError("count_tokens")


def count_message_tokens(messages: list[tuple[str, str]]) -> int:
    """Tokens of a message list: the text plus 4 per message for its role and separators."""
    return sum(count_tokens(content) + 4 for _, content in messages)


def budget_report(sections: Sections) -> dict[str, int]:
    """Tokens per section, in SECTION_ORDER, plus "total".

    {"system": 41, "tools": 193, "history": 41, "tool_result": 14475, "total": 14750}
    A section missing from `sections` counts as 0 tokens (use sections.get(name, "")).
    """
    # TODO
    raise NotImplementedError("budget_report")


def fit_to_budget(sections: Sections, budget: int) -> Sections:
    """Fill the budget in SECTION_ORDER. A section that fits is kept whole; the first one that does not
    is cut to the tokens left (with CUT_MARKER); every section after it is left empty.

    Walk SECTION_ORDER with `left = budget`:
    - the section fits (count_tokens(text) <= left): keep it whole and subtract its tokens from `left`
    - it does not fit: keep its first `room = left - count_tokens(CUT_MARKER)` tokens plus CUT_MARKER
      (ENCODING.decode(ENCODING.encode(text)[:room]) + CUT_MARKER), or "" when room <= 0; then left = 0,
      so every later section becomes ""
    The result has every name of SECTION_ORDER as a key. The order is also the priority: the system
    prompt is never cut before the tool output.
    """
    # TODO
    raise NotImplementedError("fit_to_budget")


def build_messages(sections: Sections, question: str) -> list[tuple[str, str]]:
    """System prompt and tool definitions first; history and tool output as delimited blocks; the
    question LAST, after the long material, where the model reads it with everything else in view."""
    system = sections.get("system", "")
    if sections.get("tools"):
        system += "\n\n## Tools you can call\n" + sections["tools"]
    blocks = [f"<{name}>\n{sections[name]}\n</{name}>" for name in ("history", "tool_result") if sections.get(name)]
    return [("system", system), ("user", "\n\n".join(blocks + [f"Question: {question}"]))]


# ------------------------------------------------------------------ 2. long tool results
def compact_orders(account: dict) -> str:
    """The raw API response projected onto what support needs: one line per order.

        N-5104 | 2026-02-05 | delivered | 12x Barako Bold, 1x Hand Grinder Pro | total 8130 PHP | J&T Express JJ9682283881 | last: Delivered, signed by L. Navarro (Makati)

    Header line first: account name, id and contact name, for example
        Account Bayani Café (acct_88213), contact Marco Reyes. 30 orders, oldest first:
    Then one line per order in account["orders"], the fields joined with " | ":
        order_id, the date part of created_at ([:10]), status,
        the items as "<qty>x <name>" joined with ", ",
        "total <totals.grand_total> <currency>", "<shipping.carrier> <shipping.tracking_number>",
        "last: <detail> (<location>)" of the LAST event in shipping.events
    Leave out everything support never asks about: warehouse bins, links, weights, payment references.
    Open account.json and look at one order before you start.
    """
    # TODO
    raise NotImplementedError("compact_orders")


# ------------------------------------------------------------------ 3. isolation
def run_subagent(llm: BaseChatModel, question: str, material: str) -> tuple[str, int]:
    """A separate call with its own, clean context: it reads the raw material and returns only findings.
    Returns (findings, tokens the sub-agent used: its input messages plus its answer).

    1. messages = [("system", SUBAGENT_PROMPT),
                   ("user", f"<material>\\n{material}\\n</material>\\n\\nQuestion: {question}")]
    2. findings = llm.invoke(messages).text, stripped of surrounding whitespace
    3. tokens used = count_message_tokens(messages) + count_tokens(findings)
    """
    # TODO
    raise NotImplementedError("run_subagent")


# ------------------------------------------------------------------ 4. position and noise
def needle_context(needle: str, distractors: list[str], n: int, position: str) -> list[str]:
    """n distractor notes with the needle placed at the "start", in the "middle" (index n // 2) or at the "end".

    Take the FIRST n distractors (a new list: do not change `distractors`) and insert the needle at
    index 0, n // 2 or n. The result has n + 1 notes.
    """
    # TODO
    raise NotImplementedError("needle_context")


# ------------------------------------------------------------------ 5. measuring
def recalled(answer: str, keywords: list[str]) -> bool:
    """Every keyword appears in the answer. Case and thousands separators are ignored (7,600 == 7600)."""
    text = answer.lower().replace(",", "")
    return all(keyword.lower().replace(",", "") in text for keyword in keywords)


def evaluate(llm: BaseChatModel, builder: Builder, probes: list[dict]) -> dict:
    """Run every probe through one way of building the context.

    Returns accuracy, the mean tokens of the MAIN call, the mean tokens of everything
    (main call + what the builder spent elsewhere, such as a sub-agent), and the missed questions.

    For each probe:
      sections, side_tokens = builder(probe["question"])
      messages = build_messages(sections, probe["question"]); tokens = count_message_tokens(messages)
      add tokens to the main total, and tokens + side_tokens to the overall total
      it is a hit when recalled(llm.invoke(messages).text, probe["expect_keywords"])
    Return {"accuracy": hits / number of probes,
            "main_tokens": round(main total / number of probes),
            "total_tokens": round(overall total / number of probes),
            "missed": [the questions that were not answered]}
    """
    # TODO
    raise NotImplementedError("evaluate")


# ------------------------------------------------------------------ the experiments
def base_sections(tool_result: str) -> Sections:
    return {"system": SYSTEM, "tools": json.dumps(TOOLS), "history": HISTORY, "tool_result": tool_result}


def build_strategies(llm: BaseChatModel, account: dict, budget: int = 4000) -> dict[str, Builder]:
    """Four ways to put the same order lookup into the context."""
    raw = json.dumps(account, ensure_ascii=False)
    compact = compact_orders(account)

    def subagent(question: str) -> tuple[Sections, int]:
        findings, used = run_subagent(llm, question, raw)
        return base_sections(f"Findings from the order lookup: {findings}"), used

    return {
        "raw dump": lambda q: (base_sections(raw), 0),
        f"raw, cut to {budget}": lambda q: (fit_to_budget(base_sections(raw), budget), 0),
        "compacted": lambda q: (base_sections(compact), 0),
        "sub-agent": subagent,
    }


def noise_sweep(llm: BaseChatModel, needles: list[dict], distractors: list[str],
                sizes: tuple[int, ...] = (0, 200, 1000),
                positions: tuple[str, ...] = ("start", "middle", "end")) -> list[dict]:
    """Accuracy and tokens for every (number of distractors, position of the needle)."""
    rows = []
    for n in sizes:
        for position in positions if n else ("start",):  # with no noise, every position is the same
            def builder(question: str, n=n, position=position) -> tuple[Sections, int]:
                needle = next(item["note"] for item in needles if item["question"] == question)
                notes = needle_context(needle, distractors, n, position)
                return {"system": SYSTEM, "tool_result": "\n".join(notes)}, 0
            result = evaluate(llm, builder, needles)
            rows.append({"distractors": n, "position": position if n else "-", **result})
    return rows


def main() -> None:
    account = json.loads(ACCOUNT.read_text(encoding="utf-8"))
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    llm = get_chat_model(temperature=0)

    raw = json.dumps(account, ensure_ascii=False)
    print(f"The order lookup returned {len(raw.encode()):,} bytes. Where the tokens of one call go:\n")
    for label, sections in [("raw dump", base_sections(raw)), ("compacted", base_sections(compact_orders(account)))]:
        report = budget_report(sections)
        print(f"  {label:<10}" + "  ".join(f"{name} {tokens:>6,}" for name, tokens in report.items()))

    print(f"\n{len(cases['probes'])} questions about the account:\n")
    print(f"{'context':<18}{'accuracy':>9}{'main tokens':>13}{'total tokens':>14}   missed")
    for name, builder in build_strategies(llm, account).items():
        r = evaluate(llm, builder, cases["probes"])
        print(f"{name:<18}{r['accuracy']:>9.0%}{r['main_tokens']:>13,}{r['total_tokens']:>14,}   "
              f"{'; '.join(q[:34] for q in r['missed']) or '-'}")

    print(f"\nOne fact among look-alike notes of other customers ({len(cases['needles'])} questions per row):\n")
    print(f"{'distractors':>11}  {'position':<8}{'accuracy':>9}{'tokens':>8}   missed")
    for row in noise_sweep(llm, cases["needles"], cases["distractors"]):
        print(f"{row['distractors']:>11}  {row['position']:<8}{row['accuracy']:>9.0%}{row['main_tokens']:>8,}   "
              f"{'; '.join(q[:34] for q in row['missed']) or '-'}")


if __name__ == "__main__":
    main()
