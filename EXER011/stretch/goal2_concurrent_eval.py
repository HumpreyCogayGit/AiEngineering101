"""EXER011 stretch goal 2 — run the EXER008 evaluation concurrently.

    uv run python EXER011/stretch/goal2_concurrent_eval.py

An evaluation is many independent calls: the ideal case for concurrency.
The same 16 tickets are classified one after another, then with at most 4
requests in flight, and both must give the same accuracy.
"""

from __future__ import annotations

import asyncio
import time

from aicourse.llm import get_async_llm_client, get_llm_client, model_params
from aicourse.settings import get_settings
from aicourse.stretch import solution_module

prompts = solution_module(__file__, "prompts.py", exercise="EXER008")


async def evaluate_concurrently(builder, dataset: list[dict], concurrency: int = 4) -> float:
    client = get_async_llm_client()
    semaphore = asyncio.Semaphore(concurrency)

    async def classify(row: dict) -> bool:
        async with semaphore:  # at most `concurrency` requests in flight
            response = await client.chat.completions.create(
                model=get_settings().chat_model,
                messages=builder(row["text"]),
                **model_params(temperature=0),
            )
        return prompts.normalize_label(response.choices[0].message.content or "") == row["label"]

    results = await asyncio.gather(*(classify(row) for row in dataset))
    return sum(results) / len(results)


def main() -> None:
    data = prompts.load_dataset()
    builder = prompts.build_messages_v3
    model_params(temperature=0)  # warm the capability cache, so neither timing pays for the detection call

    start = time.perf_counter()
    sequential = prompts.evaluate(get_llm_client(), builder, data)
    sequential_time = time.perf_counter() - start

    start = time.perf_counter()
    concurrent = asyncio.run(evaluate_concurrently(builder, data, concurrency=4))
    concurrent_time = time.perf_counter() - start

    print(f"sequential    accuracy={sequential:.0%}  {sequential_time:5.1f}s")
    print(f"concurrent x4 accuracy={concurrent:.0%}  {concurrent_time:5.1f}s")
    print(f"speed-up: {sequential_time / concurrent_time:.1f}x for {len(data)} tickets")


if __name__ == "__main__":
    main()
