"""EXER004 stretch goal 2 — price one prompt for two models.

    uv run python EXER004/stretch/goal2_price_table.py

The call is made once. The token counts are then priced with each row of a
small table, which is how you compare models before switching: same usage,
different prices. (A different model also tokenizes and answers differently,
so treat the result as an estimate.)
"""

from __future__ import annotations

from aicourse.stretch import solution_module

base = solution_module(__file__, "sdk_basics.py")

# USD per 1 million tokens: (input, output). EXAMPLE numbers only.
# Replace them with the rows of your provider's pricing page; a local model is (0, 0).
PRICES: dict[str, tuple[float, float]] = {
    "small model": (0.40, 1.60),
    "large model": (2.00, 8.00),
    "local model": (0.00, 0.00),
}


def price_for_all(prompt_tokens: int, completion_tokens: int) -> dict[str, float]:
    return {
        name: base.estimate_cost(prompt_tokens, completion_tokens, input_price, output_price)
        for name, (input_price, output_price) in PRICES.items()
    }


def main() -> None:
    result = base.ask(base.make_client(), "Explain what an API is in three sentences.")
    print(f"prompt_tokens={result.prompt_tokens} completion_tokens={result.completion_tokens}\n")
    costs = price_for_all(result.prompt_tokens, result.completion_tokens)
    for name, cost in costs.items():
        print(f"  {name:<12} ${cost:.6f} per call   ${cost * 100_000:>9,.2f} per 100,000 calls")
    cheapest = min((c for c in costs.values() if c > 0), default=0)
    if cheapest:
        print(f"\nThe large model costs {costs['large model'] / cheapest:.0f}x the small one for the same tokens.")


if __name__ == "__main__":
    main()
