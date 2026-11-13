"""EXER014 — Structured Output in LangChain.

`llm.with_structured_output(PydanticModel)` turns any chat model into a
Runnable that returns an instance of your model. Validation is still your
job: the schema guarantees the SHAPE, not that the numbers add up.

    uv run python EXER014/starter/invoice_parser.py
    uv run python EXER014/check.py
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

    # TODO: add these fields, each with a helpful Field(description=...):
    #   invoice_number: str   — exactly as written
    #   vendor: str           — who issued it
    #   date: str             — ISO format YYYY-MM-DD
    #   currency: str         — ISO code such as USD
    #   line_items: list[LineItem]
    #   total: float          — the total as STATED on the invoice
    pass


def build_parser(llm: BaseChatModel) -> Runnable:
    """Return llm.with_structured_output(Invoice)."""
    # TODO
    raise NotImplementedError("build_parser")


def parse_invoice(parser: Runnable, text: str) -> Invoice:
    """Invoke the parser with a system instruction and the invoice text.

    Runnables accept a list of (role, content) tuples:
        [("system", "Extract the invoice data. ..."), ("human", text)]
    """
    # TODO
    raise NotImplementedError("parse_invoice")


def validate_totals(invoice: Invoice, tolerance: float = 0.01) -> bool:
    """Business rule: the sum of item.amount must equal invoice.total (within tolerance)."""
    # TODO
    raise NotImplementedError("validate_totals")


def parse_safely(llm: BaseChatModel, text: str) -> tuple[Invoice | None, str | None]:
    """Use llm.with_structured_output(Invoice, include_raw=True).

    The result is a dict {"raw": AIMessage, "parsed": Invoice | None, "parsing_error": Exception | None}.
    Return (None, str(error)) if parsing failed, else (parsed, None).
    """
    # TODO
    raise NotImplementedError("parse_safely")


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
