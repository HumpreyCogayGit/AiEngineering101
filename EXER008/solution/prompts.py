"""EXER008 — Prompt Engineering Basics (reference solution).

We build a support-ticket classifier three times, each prompt better than
the last, and MEASURE the accuracy of each on a labelled dataset.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from aicourse.llm import get_openai_client, model_params
from aicourse.settings import get_settings

LABELS = ["billing", "technical", "account", "other"]
DATASET = Path(__file__).resolve().parent.parent / "tickets.json"


# ------------------------------------------------------------- v1: naive
def build_messages_v1(ticket: str) -> list[dict]:
    """The prompt most people write first. Vague: no list of labels, no format."""
    return [{"role": "user", "content": f"What kind of support ticket is this? {ticket}"}]


# ------------------------------------------------- v2: clear instructions
SYSTEM_V2 = f"""You are a support-ticket classifier.

Classify the ticket inside the <ticket> tags into exactly ONE category:
- billing: payments, charges, refunds, invoices, receipts, plans and pricing
- technical: bugs, errors, crashes, performance, sync or upload problems
- account: login, password, profile, users, permissions, deleting an account
- other: anything else (questions about the company, feedback, jobs, ...)

Respond with the category name only, in lowercase, with no punctuation.
Allowed answers: {", ".join(LABELS)}"""


def build_messages_v2(ticket: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_V2},
        {"role": "user", "content": f"<ticket>\n{ticket}\n</ticket>"},
    ]


# ------------------------------------------------------- v3: few-shot
FEW_SHOT_EXAMPLES = [
    ("My refund hasn't arrived after two weeks.", "billing"),
    ("Images don't load in the mobile app.", "technical"),
    ("I can't log in with my Google account.", "account"),
    ("Where are you headquartered?", "other"),
]


def build_messages_v3(ticket: str) -> list[dict]:
    """v2 plus worked examples as user/assistant message pairs."""
    messages = [{"role": "system", "content": SYSTEM_V2}]
    for example, label in FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": f"<ticket>\n{example}\n</ticket>"})
        messages.append({"role": "assistant", "content": label})
    messages.append({"role": "user", "content": f"<ticket>\n{ticket}\n</ticket>"})
    return messages


# ---------------------------------------------------------- run + measure
def normalize_label(text: str) -> str:
    """Map a free-text answer to one of LABELS ('unknown' if none matches)."""
    cleaned = text.strip().lower().strip(".!\"' ")
    if cleaned in LABELS:
        return cleaned
    for label in LABELS:
        if label in cleaned:
            return label
    return "unknown"


def classify(client, messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=get_settings().chat_deployment,
        messages=messages,
        **model_params(temperature=0),
    )
    return normalize_label(response.choices[0].message.content or "")


def load_dataset() -> list[dict]:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def evaluate(client, builder: Callable[[str], list[dict]], dataset: list[dict]) -> float:
    """Accuracy of a prompt builder on the dataset (0.0 – 1.0)."""
    correct = sum(classify(client, builder(row["text"])) == row["label"] for row in dataset)
    return correct / len(dataset)


def main() -> None:
    client = get_openai_client()
    data = load_dataset()
    for name, builder in [("v1 naive", build_messages_v1), ("v2 instructions", build_messages_v2),
                          ("v3 few-shot", build_messages_v3)]:
        print(f"{name:<16} accuracy = {evaluate(client, builder, data):.0%}")
    print("\nWhat v1 actually answers:")
    resp = client.chat.completions.create(model=get_settings().chat_deployment,
                                          messages=build_messages_v1(data[0]["text"]))
    print(" ", resp.choices[0].message.content[:200])


if __name__ == "__main__":
    main()
