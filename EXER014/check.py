"""EXER014 checks. Run:  uv run python EXER014/check.py"""

from pathlib import Path

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("invoice_parser.py")
INVOICES = Path(__file__).parent / "invoices"


def sample_invoice(total=81.75):
    return mod.Invoice(
        invoice_number="BL-1", vendor="Brightleaf", date="2026-04-12", currency="USD",
        line_items=[mod.LineItem(description="paper", quantity=10, unit_price=4.5),
                    mod.LineItem(description="pens", quantity=3, unit_price=6.0),
                    mod.LineItem(description="stapler", quantity=1, unit_price=18.75)],
        total=total,
    )


@checker.check("Invoice has all six fields, each with a description")
def _():
    fields = mod.Invoice.model_fields
    expected = {"invoice_number", "vendor", "date", "currency", "line_items", "total"}
    if not fields:
        raise NotImplementedError("Invoice fields")
    assert expected <= set(fields), f"missing: {expected - set(fields)}"
    undocumented = [n for n, f in fields.items() if not f.description]
    assert not undocumented, f"add Field(description=...) to: {undocumented}"


@checker.check("validate_totals() accepts a correct invoice and rejects a wrong one")
def _():
    assert mod.validate_totals(sample_invoice()) is True
    assert mod.validate_totals(sample_invoice(total=99.0)) is False


@checker.check("build_parser() + parse_invoice() return an Invoice")
def _():
    llm = fake_chat_model(structured=[sample_invoice()])
    result = mod.parse_invoice(mod.build_parser(llm), "invoice text")
    assert isinstance(result, mod.Invoice)


@checker.check("all three sample invoices parse and their totals add up  [live API]")
def _():
    parser = mod.build_parser(get_chat_model(temperature=0))
    expected = {"invoice_001.txt": 81.75, "invoice_002.txt": 605.0, "invoice_003.txt": 84.0}
    for name, total in expected.items():
        inv = mod.parse_invoice(parser, (INVOICES / name).read_text())
        assert abs(inv.total - total) < 0.01, f"{name}: total {inv.total}"
        assert mod.validate_totals(inv), f"{name}: items don't add up: {inv.line_items}"


@checker.check("dates are normalized to YYYY-MM-DD  [live API]")
def _():
    inv = mod.parse_invoice(mod.build_parser(get_chat_model(temperature=0)),
                            (INVOICES / "invoice_001.txt").read_text())
    assert inv.date == "2026-04-12", inv.date


checker.run()
