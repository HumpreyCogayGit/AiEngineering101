"""EXER006 stretch goal 2 — summarize the dropped turns instead of deleting them.

    uv run python EXER006/stretch/goal2_summarize_dropped.py

trim_history() forgets everything outside the window. Here the turns that
would be dropped are first condensed by the model into one short message,
which stays in the history. It costs one extra call and keeps the gist:
the trade-off from the lecture's table, in code.
"""

from __future__ import annotations

from aicourse.llm import get_llm_client, model_params
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "content_blocks.py")

SUMMARY_PREFIX = "Summary of the earlier conversation: "


def summarize(client, messages: list[dict]) -> str:
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    response = client.chat.completions.create(
        model=get_settings().chat_model,
        messages=[
            {"role": "system", "content": "Summarize this conversation in at most 60 words. "
                                          "Keep names, numbers and decisions. No preamble."},
            {"role": "user", "content": transcript},
        ],
        **model_params(temperature=0),
    )
    return response.choices[0].message.content or ""


def trim_with_summary(client, messages: list[dict], max_tokens: int, summary_tokens: int = 120) -> list[dict]:
    """Like trim_history, but the dropped turns survive as one summary message."""
    # Leave room for the summary, then trim as before.
    kept = base.trim_history(messages, max_tokens - summary_tokens)
    system, recent = kept[:1], kept[1:]
    old = [m for m in messages if m["role"] != "system"][: len(messages) - len(kept)]
    if not old:
        return kept  # everything fits: nothing to summarize, no extra call
    summary = {"role": "system", "content": SUMMARY_PREFIX + summarize(client, old)}
    return system + [summary] + recent


def main() -> None:
    client = get_llm_client()
    history = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Hi, I'm Ada. My order number is 4471 and I ordered a Hand Grinder Pro."},
        {"role": "assistant", "content": "Thanks Ada, I have order 4471 for the Hand Grinder Pro."},
    ]
    for i in range(12):
        history.append({"role": "user", "content": f"Unrelated question {i}: " + "blah " * 30})
        history.append({"role": "assistant", "content": f"Answer {i}: " + "ok " * 30})
    history.append({"role": "user", "content": "What was my order number again?"})

    plain = base.trim_history(history, 400)
    smart = trim_with_summary(client, history, 400)
    print(f"{len(history)} messages -> trim: {len(plain)}, trim + summary: {len(smart)}")
    print("Summary message:", smart[1]["content"])
    for label, messages in (("trim only     ", plain), ("trim + summary", smart)):
        answer = client.chat.completions.create(model=get_settings().chat_model, messages=messages)
        print(f"{label}: {answer.choices[0].message.content}")


if __name__ == "__main__":
    main()
