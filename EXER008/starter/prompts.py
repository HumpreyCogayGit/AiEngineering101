"""EXER008 — Prompt Engineering Basics.

Build a support-ticket classifier three times, each prompt better than the
last, and MEASURE the accuracy of each on tickets.json.

    uv run python EXER008/starter/prompts.py
    uv run python EXER008/check.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from aicourse.llm import get_llm_client, model_params
from aicourse.settings import get_settings

LABELS = ["billing", "technical", "account", "other"]
DATASET = Path(__file__).resolve().parent.parent / "tickets.json"


# ------------------------------------------------------------- v1: naive
def build_messages_v1(ticket: str) -> list[dict]:
    """The prompt most people write first. Vague: no list of labels, no format. (Given.)"""
    return [{"role": "user", "content": f"What kind of support ticket is this? {ticket}"}]


# ------------------------------------------------- v2: clear instructions
# TODO: write SYSTEM_V2. It must:
#   - say what the assistant is (a support-ticket classifier)
#   - list EVERY label in LABELS with a short description of what belongs in it
#   - say the ticket will be inside <ticket> ... </ticket> tags (delimiters)
#   - demand the answer be ONLY the label, lowercase, nothing else
SYSTEM_V2 = """TODO"""


def build_messages_v2(ticket: str) -> list[dict]:
    """[system: SYSTEM_V2, user: the ticket wrapped in <ticket> ... </ticket>]"""
    # TODO
    raise NotImplementedError("build_messages_v2")


# ------------------------------------------------------- v3: few-shot
# TODO: write at least 3 (ticket, label) examples — NOT copied from tickets.json
FEW_SHOT_EXAMPLES: list[tuple[str, str]] = []


def build_messages_v3(ticket: str) -> list[dict]:
    """Like v2, but between the system message and the real ticket insert each
    example as a PAIR of messages:
        user:      <ticket>example text</ticket>
        assistant: label
    """
    # TODO
    raise NotImplementedError("build_messages_v3")


# ---------------------------------------------------------- run + measure
def normalize_label(text: str) -> str:
    """Map a free-text answer to one of LABELS, or "unknown".

    "Billing."  -> "billing"
    "This is a technical issue" -> "technical"
    "no idea" -> "unknown"
    """
    # TODO
    raise NotImplementedError("normalize_label")


def classify(client, messages: list[dict]) -> str:
    """Call the model with temperature=0 and return normalize_label(reply).

    Pass it as `**model_params(temperature=0)`: that sends temperature=0 when your
    model accepts it and leaves it out for reasoning models (gpt-5 family).
    """
    # TODO
    raise NotImplementedError("classify")


def load_dataset() -> list[dict]:
    return json.loads(DATASET.read_text(encoding="utf-8"))


def evaluate(client, builder: Callable[[str], list[dict]], dataset: list[dict]) -> float:
    """Accuracy of a prompt builder on the dataset (0.0 – 1.0)."""
    correct = sum(classify(client, builder(row["text"])) == row["label"] for row in dataset)
    return correct / len(dataset)


def main() -> None:
    client = get_llm_client()
    data = load_dataset()
    for name, builder in [("v1 naive", build_messages_v1), ("v2 instructions", build_messages_v2),
                          ("v3 few-shot", build_messages_v3)]:
        print(f"{name:<16} accuracy = {evaluate(client, builder, data):.0%}")
    print("\nWhat v1 actually answers:")
    resp = client.chat.completions.create(model=get_settings().chat_model,
                                          messages=build_messages_v1(data[0]["text"]))
    print(" ", resp.choices[0].message.content[:200])


if __name__ == "__main__":
    main()
