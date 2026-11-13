"""EXER014 — Structured Output in LangChain (reference solution).

`llm.with_structured_output(PydanticModel)` turns any chat model into a
Runnable that returns an instance of your model. Validation is still your
job: the schema guarantees the SHAPE, not that the numbers add up.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from aicourse.llm import get_chat_model

INVOICES = Path(__file__).resolve().parent.parent / "invoices"


class LineItem(BaseModel):
    description: str = Field(description="What was bought")
    quantity: float = Field(description="Number of units (hours count as units)")
    unit_price: float = Field(description="Price of one unit, without currency symbol")

    @property
    def amount(self) -> float:
        return self.quantity * self.unit_price


class Invoice(BaseModel):
    """An invoice extracted from text."""

    invoice_number: str = Field(description="The invoice number or id, exactly as written")
    vendor: str = Field(description="Company or person who issued the invoice")
    date: str = Field(description="Issue date in ISO format YYYY-MM-DD")
    currency: str = Field(description="ISO currency code, e.g. USD")
    line_items: list[LineItem] = Field(description="Every billed item, including fees")
    total: float = Field(description="The total amount due as stated on the invoice")


def build_parser(llm: BaseChatModel) -> Runnable:
    return llm.with_structured_output(Invoice)


def parse_invoice(parser: Runnable, text: str) -> Invoice:
    return parser.invoke(
        [
            # The schema fixes the shape; rules about values (the date format) are stated
            # here too, because not every provider shows the field descriptions to the model.
            ("system", "Extract the invoice data. Use only information present in the text. "
                       "Write dates as YYYY-MM-DD and the currency as an ISO code such as USD."),
            ("human", text),
        ]
    )


def validate_totals(invoice: Invoice, tolerance: float = 0.01) -> bool:
    """Business rule: line items must add up to the stated total."""
    computed = sum(item.amount for item in invoice.line_items)
    return abs(computed - invoice.total) <= tolerance


def parse_safely(llm: BaseChatModel, text: str) -> tuple[Invoice | None, str | None]:
    """include_raw=True never raises on bad output; it returns the error instead."""
    runnable = llm.with_structured_output(Invoice, include_raw=True)
    result = runnable.invoke([("system", "Extract the invoice data."), ("human", text)])
    if result["parsing_error"] is not None:
        return None, str(result["parsing_error"])
    return result["parsed"], None


def main() -> None:
    parser = build_parser(get_chat_model(temperature=0))
    for path in sorted(INVOICES.glob("*.txt")):
        invoice = parse_invoice(parser, path.read_text(encoding="utf-8"))
        status = "OK" if validate_totals(invoice) else "TOTAL MISMATCH"
        print(f"\n{path.name}: {invoice.invoice_number} | {invoice.vendor} | {invoice.date} | "
              f"{invoice.currency} {invoice.total:.2f}  [{status}]")
        for item in invoice.line_items:
            print(f"   {item.quantity:>5} x {item.description:<35} @ {item.unit_price:>7.2f}")


if __name__ == "__main__":
    main()
