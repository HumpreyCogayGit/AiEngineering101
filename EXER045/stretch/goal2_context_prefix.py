"""EXER045 stretch goal 2 — EXER040's context layout, measured for prompt caching (EXER040).

    uv run python EXER045/stretch/goal2_context_prefix.py

EXER040 put the question LAST, after the long material, because models read it
better there. Every question about the same account then starts with the same
~2,000 tokens. Does the provider reuse them? It depends on WHERE they are.

Five EXER040 probe questions are sent in three layouts:

    exer040          system: prompt + tools     user: material + question
    question first   system: prompt + tools     user: question + material
    material first   system: prompt + tools + material    user: question

and the script prints the cached prompt tokens the provider reports. When this
lesson was written, one Azure deployment reused a prefix only up to the end of
an identical system message: identical material in the user message was not
reused unless the whole prompt matched. Your provider may differ. That is the
point: measure before you rearrange prompts for a cache.
"""

from __future__ import annotations

import json
import time
import uuid

from aicourse.llm import get_llm_client, model_params
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

ctx = solution_module(__file__, "context_engineering.py", exercise="EXER040")


def split(sections: dict, question: str) -> tuple[str, str]:
    (_, system), (_, user) = ctx.build_messages(sections, question)
    return system, user.rsplit("\n\nQuestion:", 1)[0]


LAYOUTS = {
    "exer040": lambda s, q: ctx.build_messages(s, q),
    "question first": lambda s, q: [("system", split(s, q)[0]), ("user", f"Question: {q}\n\n{split(s, q)[1]}")],
    "material first": lambda s, q: [("system", "\n\n".join(split(s, q))), ("user", f"Question: {q}")],
}


def run(label: str, layout, probes: list[dict], sections: dict) -> None:
    client, model = get_llm_client(), get_settings().chat_model
    prompt_total = cached_total = 0
    for probe in probes:
        # A fresh reference on every question: a prompt the provider has never seen as a whole, so any
        # cached tokens are a reused PREFIX, not a repeat of an earlier run.
        question = f"{probe['question']} [ref {uuid.uuid4().hex[:8]}]"
        messages = [{"role": role, "content": text} for role, text in layout(sections, question)]
        usage = client.chat.completions.create(model=model, messages=messages, **model_params(max_tokens=300)).usage
        details = getattr(usage, "prompt_tokens_details", None)
        cached = getattr(details, "cached_tokens", None) or 0
        prompt_total += usage.prompt_tokens
        cached_total += cached
        print(f"  {label:<15} prompt {usage.prompt_tokens:>5}  cached {cached:>5}  {probe['question'][:48]}")
        time.sleep(1)
    print(f"  {label:<15} {cached_total / prompt_total:.0%} of {prompt_total} prompt tokens came from the cache\n")


def main() -> None:
    account = json.loads(ctx.ACCOUNT.read_text(encoding="utf-8"))
    probes = json.loads(ctx.CASES.read_text(encoding="utf-8"))["probes"][:5]
    sections = ctx.base_sections(ctx.compact_orders(account))
    for label, layout in LAYOUTS.items():
        run(label, layout, probes, sections)
    print("No cached tokens at all? Your provider may not report them (a local Ollama does not), or the "
          "prompt is below its minimum length for caching.")


if __name__ == "__main__":
    main()
