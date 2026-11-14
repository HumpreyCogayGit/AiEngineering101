"""EXER008 stretch goal 1 — a fourth prompt that explains its label, measured.

    uv run python EXER008/stretch/goal1_explain_label.py

v4 asks for a one-sentence reason BEFORE the label. Does thinking first help?
Do not guess: measure it against v3 on the same dataset. The answer depends
on your model, which is the point of measuring.

The reason is written first on purpose. A model writes left to right, so a
reason that comes after the label can only justify a decision already made.
"""

from __future__ import annotations

from aicourse.llm import get_llm_client, model_params
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "prompts.py")

SYSTEM_V4 = base.SYSTEM_V2.replace(
    "Respond with the category name only, in lowercase, with no punctuation.",
    "Respond with exactly two lines:\nreason: <one short sentence>\nlabel: <the category name, lowercase>",
)
assert SYSTEM_V4 != base.SYSTEM_V2, "the v2 prompt changed: update the replace() above"


def build_messages_v4(ticket: str) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_V4}]
    for example, label in base.FEW_SHOT_EXAMPLES:
        messages.append({"role": "user", "content": f"<ticket>\n{example}\n</ticket>"})
        messages.append({"role": "assistant", "content": f"reason: (example)\nlabel: {label}"})
    messages.append({"role": "user", "content": f"<ticket>\n{ticket}\n</ticket>"})
    return messages


def parse_v4(text: str) -> tuple[str, str]:
    """Return (label, reason). The label is read from its own line, never from the reason."""
    label, reason = "unknown", ""
    for line in text.splitlines():
        key, _, value = line.partition(":")
        if key.strip().lower() == "reason":
            reason = value.strip()
        elif key.strip().lower() == "label":
            label = base.normalize_label(value)
    return label, reason


def classify_v4(client, ticket: str) -> tuple[str, str]:
    response = client.chat.completions.create(
        model=get_settings().chat_model, messages=build_messages_v4(ticket), **model_params(temperature=0)
    )
    return parse_v4(response.choices[0].message.content or "")


def main() -> None:
    client = get_llm_client()
    data = base.load_dataset()
    correct = 0
    for row in data:
        label, reason = classify_v4(client, row["text"])
        correct += label == row["label"]
        if label != row["label"]:
            print(f"  MISS expected={row['label']} got={label}: {row['text'][:60]}\n       reason: {reason}")
    print(f"v3 few-shot       accuracy = {base.evaluate(client, base.build_messages_v3, data):.0%}")
    print(f"v4 reason + label accuracy = {correct / len(data):.0%}")
    label, reason = classify_v4(client, data[0]["text"])
    print(f"\nExample: {data[0]['text']}\n  reason: {reason}\n  label : {label}")


if __name__ == "__main__":
    main()
