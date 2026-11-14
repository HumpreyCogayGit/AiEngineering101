# EXER014 — Structured Output in LangChain

**Module 2 · LangChain** · Lecture: [Lecture/lectures/lec014.html](../Lecture/lectures/lec014.html)

## Goal

Use `with_structured_output` to turn unstructured documents into validated
Python objects, and add business-rule validation on top of schema validation.

## The project

An invoice parser for three very different invoice formats in [invoices/](invoices/):
a formal table, a casual email, and a hosting statement.

## Tasks

Complete the TODOs in `starter/invoice_parser.py`:

1. The `Invoice` Pydantic model (fields **with descriptions** — they guide the model)
2. `build_parser`, `parse_invoice`
3. `validate_totals` — do the line items add up to the stated total?
4. `parse_safely` — `include_raw=True` for graceful failure

## Run it

```bash
uv run python EXER014/starter/invoice_parser.py
uv run python EXER014/check.py
```

## Success criteria

- [ ] All three invoices parse into `Invoice` objects with correct totals
- [ ] Dates in three different formats all come out as `YYYY-MM-DD`
- [ ] Every invoice prints `[OK]` — the line items add up
- [ ] All 5 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Make the parser return a list of problems (parse errors and broken business rules) instead of raising. *Done when:* the three invoices print `ACCEPT`, and an invoice with a wrong total prints `REVIEW` with the reason.
2. **Connect (EXER012).** Parse the invoices concurrently with `batch`. *Done when:* the results come back in input order, and the script prints the speed-up over one at a time.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER014/stretch/goal1_validation_problems.py
uv run python EXER014/stretch/goal2_batch_invoices.py
```
