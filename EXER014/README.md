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
