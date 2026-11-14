"""EXER017 stretch goal 2 — a Pydantic `args_schema` with a currency enum.

    uv run python EXER017/stretch/goal2_args_schema.py

`@tool` builds the schema from the signature: `from_currency: str` tells the
model "any string". An explicit `args_schema` can say more: the allowed
values (an enum), a minimum, a description per argument. Two things improve:

- the model SEES the allowed codes, so it stops inventing "PESO" or "€";
- a bad value is rejected before your function runs.
"""

from __future__ import annotations

import json
from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field, ValidationError

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "lc_tools.py")

# Keep this in step with base.RATES_TO_USD: a Literal needs the values written out.
Currency = Literal["USD", "EUR", "PHP", "JPY", "GBP"]
assert set(Currency.__args__) == set(base.RATES_TO_USD), "the enum and the rate table disagree"


class ConvertArgs(BaseModel):
    amount: float = Field(gt=0, description="The amount of money to convert")
    from_currency: Currency = Field(description="ISO code of the currency you have")
    to_currency: Currency = Field(description="ISO code of the currency you want")


@tool(args_schema=ConvertArgs)
def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert an amount of money between two currencies."""
    value = amount * base.RATES_TO_USD[from_currency] / base.RATES_TO_USD[to_currency]
    return f"{amount} {from_currency} = {value:.2f} {to_currency}"


def main() -> None:
    print("Schema from the signature (the exercise):")
    print(" ", json.dumps(base.convert_currency.args["from_currency"]))
    print("Schema from args_schema:")
    print(" ", json.dumps(convert_currency.args["from_currency"]))

    print("\nValid call  :", convert_currency.invoke({"amount": 2500, "from_currency": "PHP", "to_currency": "EUR"}))
    try:
        convert_currency.invoke({"amount": 2500, "from_currency": "PESO", "to_currency": "EUR"})
    except ValidationError as exc:
        print("Invalid call: rejected before the function ran ->", exc.errors()[0]["msg"])

    llm = get_chat_model(temperature=0).bind_tools([convert_currency])
    reply = llm.invoke("How much is 300 pesos (Philippine) in British pounds?")
    print("\nThe model, shown the enum, wrote:", reply.tool_calls[0]["args"] if reply.tool_calls else reply.text)


if __name__ == "__main__":
    main()
