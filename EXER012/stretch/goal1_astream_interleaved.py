"""EXER012 stretch goal 1 — `astream`: two answers, interleaved.

    uv run python EXER012/stretch/goal1_astream_interleaved.py

Every Runnable method has an async twin (ainvoke, astream, abatch). Two
`astream` calls run concurrently on one event loop, so their chunks arrive
mixed. The output shows it: lines tagged [A] and [B] alternate, which a pair
of ordinary `stream` loops could never produce.
"""

from __future__ import annotations

import asyncio

from aicourse.stretch import solution_module

base = solution_module(__file__, "lc_chat.py")


async def stream_tagged(llm, tag: str, question: str, order: list[str]) -> str:
    parts: list[str] = []
    async for chunk in llm.astream(question):
        if chunk.text:
            parts.append(chunk.text)
            order.append(tag)
            print(f"[{tag}] {chunk.text!r}")
    return "".join(parts)


async def main() -> None:
    llm = base.make_llm()
    order: list[str] = []  # which stream each chunk came from, in arrival order
    answer_a, answer_b = await asyncio.gather(
        stream_tagged(llm, "A", "Count from 1 to 12, separated by spaces.", order),
        stream_tagged(llm, "B", "Write the first 12 letters of the alphabet, separated by spaces.", order),
    )
    switches = sum(1 for previous, current in zip(order, order[1:]) if previous != current)
    print(f"\nA: {answer_a}\nB: {answer_b}")
    print(f"{len(order)} chunks, and the source changed {switches} times: the two streams really overlapped.")


if __name__ == "__main__":
    asyncio.run(main())
