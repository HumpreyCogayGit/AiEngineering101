"""EXER045 — does the provider reuse your prompt prefix? A measurement (given; uses build_messages).

    uv run python EXER045/solution/prefix_experiment.py

Sends the same long prompt (all Nimbus documents, about 1,800 tokens) three times
in two layouts and prints what the provider reports:

    stable    the documents first, the customer's name and the time last   (build_messages)
    unstable  the time first, then the documents: every prompt starts differently

Providers that cache prompt prefixes report the reused part in
usage.prompt_tokens_details.cached_tokens, usually only for prompts above a
minimum length (1,024 tokens on several providers). A local Ollama keeps its own
cache for the last prompt but reports nothing here; compare the latencies instead.
"""

from __future__ import annotations

import time
from datetime import datetime

from caching import build_messages

from aicourse.llm import get_llm_client, model_params
from aicourse.rag import load_knowledge_base
from aicourse.settings import get_settings

SYSTEM = "You are the Nimbus Coffee helpdesk. Answer in one sentence from the documents."


def unstable_messages(documents: str, customer_name: str, now: str, question: str) -> list[dict]:
    return [{"role": "system", "content": f"Current time: {now}. Customer: {customer_name}.\n\n{SYSTEM}\n\n"
                                          f"Documents:\n{documents}"},
            {"role": "user", "content": question}]


def measure(label: str, make) -> None:
    client, model = get_llm_client(), get_settings().chat_model
    for i, name in enumerate(("Ana", "Ben", "Carla"), 1):
        now = datetime.now().isoformat(timespec="microseconds")
        start = time.perf_counter()
        response = client.chat.completions.create(model=model, messages=make(name, now),
                                                  **model_params(max_tokens=400))
        details = getattr(response.usage, "prompt_tokens_details", None)
        cached = getattr(details, "cached_tokens", None)
        print(f"{label:<9} call {i}: prompt {response.usage.prompt_tokens:>5} tokens, "
              f"cached {cached if cached is not None else 'not reported':>12}, {time.perf_counter() - start:5.2f} s")


def main() -> None:
    documents = "\n\n".join(d.page_content for d in load_knowledge_base())
    question = "Is shipping free?"
    measure("unstable", lambda name, now: unstable_messages(documents, name, now, question))
    measure("stable", lambda name, now: build_messages(SYSTEM, documents, name, now, question))
    print("\nThe stable layout shares everything up to the customer's name, so from the second call on the "
          "provider can reuse it. In the unstable layout the first line differs every time.")


if __name__ == "__main__":
    main()
