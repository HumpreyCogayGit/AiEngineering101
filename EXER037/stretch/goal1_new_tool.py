"""EXER037 stretch goal 1 — one new tool, and two evaluation cases that need it.

    uv run python EXER037/stretch/goal1_new_tool.py

The new tool is `shipping_fee`. The fee rules are in shipping.md, and the
model can usually read them correctly, but "usually" is not good enough for a
price. A rule that must be exact belongs in code: the tool applies the rule,
the model only decides when to call it.

Adding a tool to the assistant takes three things, and no change to the core:
1. the tool, with a docstring the model can act on,
2. one line in the system prompt saying when to use it,
3. evaluation cases that FAIL without it (extra_eval_cases.json expects the tool).
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from langchain_core.tools import tool

from aicourse.stretch import solution_path

solution_path(__file__)  # the reference solution's files import each other by name
import assistant as assistant_module  # noqa: E402
import evaluate  # noqa: E402
import tools as tools_module  # noqa: E402

EXTRA_CASES = Path(__file__).resolve().parent / "extra_eval_cases.json"
METRO_MANILA = {"metro manila", "manila", "makati", "bgc", "taguig", "quezon city", "pasig", "mandaluyong", "pasay"}
INTERNATIONAL = {"singapore", "hong kong", "japan", "australia"}


@tool
def shipping_fee(order_total: float, destination: str, express: bool = False) -> str:
    """Exact shipping fee in pesos for an order. Use it for EVERY question about what shipping costs.
    order_total: value of the goods in pesos. destination: city, region or country.
    express: True for express shipping."""
    place = destination.strip().lower()
    if order_total < 0:
        return "Error: order_total must not be negative."
    if place in INTERNATIONAL:
        if express:
            return "Error: express shipping is not available for international orders."
        return "International shipping: ₱950 (flat)."
    if express:
        return "Express shipping: ₱250."
    if order_total > 1500:
        return "Standard shipping: ₱0 (free for orders over ₱1,500)."
    fee = 120 if place in METRO_MANILA else 180
    return f"Standard shipping: ₱{fee} ({'within Metro Manila' if fee == 120 else 'elsewhere in the Philippines'})."


PROMPT_RULE = "\n- For the cost of shipping, call shipping_fee and use its result; do not work the fee out yourself."


async def main() -> None:
    cases = json.loads(evaluate.EVAL_SET.read_text(encoding="utf-8")) + json.loads(EXTRA_CASES.read_text(encoding="utf-8"))
    assistant_module.SYSTEM_PROMPT += PROMPT_RULE
    with tempfile.TemporaryDirectory() as tmp:
        mcp_tools = await tools_module.load_mcp_tools(Path(tmp) / "notes.json")
        helpdesk = await assistant_module.Assistant(tools=tools_module.LOCAL_TOOLS + [shipping_fee] + mcp_tools).setup()
        rows = await evaluate.run_eval(helpdesk, cases)
    for row in rows:
        print(f"{'PASS' if row['passed'] else 'FAIL'}  {row['question'][:62]:<62} {', '.join(row['tools'])[:44]}"
              + (f"   <- {'; '.join(row['failures'])}" if row["failures"] else ""))
    new = rows[-2:]
    print(f"\n{sum(r['passed'] for r in rows)}/{len(rows)} passed; the two new cases: "
          f"{sum(r['passed'] for r in new)}/2, both must use shipping_fee.")


if __name__ == "__main__":
    asyncio.run(main())
