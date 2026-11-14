"""EXER014 stretch goal 1 — return a list of problems instead of raising.

    uv run python EXER014/stretch/goal1_validation_problems.py

An invoice that cannot be trusted is not an exception, it is a result: it
goes to a person, together with the reasons. So the parser returns
(invoice or None, problems). An empty list means "accept".

Three kinds of problem end up in the same list:
- the model's output did not parse           (include_raw=True, as in the exercise)
- the values break a business rule            (totals, dates, quantities)
- the invoice is suspicious                   (no line items)
"""

from __future__ import annotations

import re

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "invoice_parser.py")

SYSTEM = ("Extract the invoice data. Use only information present in the text. "
          "Write dates as YYYY-MM-DD and the currency as an ISO code such as USD.")


def business_problems(invoice) -> list[str]:
    """Every rule that fails, not only the first: a reviewer wants the whole list."""
    problems: list[str] = []
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", invoice.date):
        problems.append(f"date is not YYYY-MM-DD: {invoice.date!r}")
    if not re.fullmatch(r"[A-Z]{3}", invoice.currency):
        problems.append(f"currency is not an ISO code: {invoice.currency!r}")
    if not invoice.line_items:
        problems.append("no line items")
    for item in invoice.line_items:
        if item.quantity <= 0 or item.unit_price < 0:
            problems.append(f"impossible line item: {item.quantity} x {item.description} @ {item.unit_price}")
    if not base.validate_totals(invoice):
        computed = sum(item.amount for item in invoice.line_items)
        problems.append(f"line items add up to {computed:.2f}, but the stated total is {invoice.total:.2f}")
    return problems


def parse_with_problems(llm, text: str):
    """Never raises on bad model output. Returns (Invoice | None, [problem, ...])."""
    result = llm.with_structured_output(base.Invoice, include_raw=True).invoke(
        [("system", SYSTEM), ("human", text)]
    )
    if result["parsing_error"] is not None:
        return None, [f"output did not parse: {result['parsing_error']}"]
    return result["parsed"], business_problems(result["parsed"])


def main() -> None:
    llm = get_chat_model(temperature=0)
    texts = {path.name: path.read_text(encoding="utf-8") for path in sorted(base.INVOICES.glob("*.txt"))}
    # A faulty invoice: the stated total ($650) does not match the items ($605).
    texts["invoice_002 (wrong total)"] = texts["invoice_002.txt"].replace("$605", "$650")
    for name, text in texts.items():
        invoice, problems = parse_with_problems(llm, text)
        number = invoice.invoice_number if invoice else "?"
        print(f"{name:<28} {number:<14} {'ACCEPT' if not problems else 'REVIEW'}")
        for problem in problems:
            print(f"    - {problem}")


if __name__ == "__main__":
    main()
