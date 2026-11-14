"""EXER014 stretch goal 2 — parse the invoices concurrently with `batch` (EXER012).

    uv run python EXER014/stretch/goal2_batch_invoices.py

`with_structured_output` returns a Runnable, so it has `batch` like every
other Runnable. Three independent invoices are three independent calls:
`batch` runs them in parallel and returns the results in input order.
"""

from __future__ import annotations

import time

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "invoice_parser.py")

SYSTEM = ("Extract the invoice data. Use only information present in the text. "
          "Write dates as YYYY-MM-DD and the currency as an ISO code such as USD.")


def parse_many(parser, texts: list[str], max_concurrency: int = 3) -> list:
    inputs = [[("system", SYSTEM), ("human", text)] for text in texts]
    # return_exceptions=True: one bad invoice must not lose the other results.
    return parser.batch(inputs, config={"max_concurrency": max_concurrency}, return_exceptions=True)


def main() -> None:
    parser = base.build_parser(get_chat_model(temperature=0))
    paths = sorted(base.INVOICES.glob("*.txt"))
    texts = [path.read_text(encoding="utf-8") for path in paths]

    start = time.perf_counter()
    one_by_one = [base.parse_invoice(parser, text) for text in texts]
    sequential = time.perf_counter() - start

    start = time.perf_counter()
    batched = parse_many(parser, texts)
    concurrent = time.perf_counter() - start

    for path, invoice in zip(paths, batched):
        if isinstance(invoice, Exception):
            print(f"{path.name}: FAILED ({invoice})")
        else:
            status = "OK" if base.validate_totals(invoice) else "TOTAL MISMATCH"
            print(f"{path.name}: {invoice.invoice_number:<14} {invoice.currency} {invoice.total:>8.2f}  [{status}]")
    same = [a.invoice_number for a in one_by_one] == [b.invoice_number for b in batched if not isinstance(b, Exception)]
    print(f"\none by one: {sequential:.1f}s   batch: {concurrent:.1f}s   "
          f"speed-up {sequential / concurrent:.1f}x   same order: {same}")


if __name__ == "__main__":
    main()
