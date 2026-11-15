# EXER043 — Safe Side Effects

**Module 9 · Running in Production** · Lecture: [Lecture/lectures/lec043.html](../Lecture/lectures/lec043.html)

## Goal

Make a tool that moves money safe to run more than once. Kill an agent in the middle of a refund,
resume it, and prove from the audit log that the customer was refunded once.

## The project

| File | Status | Your work |
|---|---|---|
| `refunds.py` | TODO | `idempotency_key`, `validate_refund`, `issue_refund`, `make_refund_tool` |

Given: a fake `PaymentGateway` that counts the money that really moved (and can "crash" right after
moving it), and a SQLite `Ledger` with an audit table.

```
model decides   AIMessage(tool_calls=[refund_order(NC-1042, 3450), id=call_7])   ← checkpointed
code commits    key = refund:<thread>:call_7 → validate → ledger "pending" → gateway(key) → ledger "done"
                                                                     every step → audit row
```

## Run it

```bash
uv run python EXER043/starter/refunds.py    # a real agent refunds, crashes after paying, and is resumed
uv run python EXER043/check.py
```

## Success criteria

- [ ] The same decision (thread and tool call id) always gives the same idempotency key
- [ ] A refund is refused for an unknown order, a non-positive amount, or more than is left to refund
- [ ] Calling `issue_refund` twice with one key moves money once and returns the same answer
- [ ] After a crash between "money moved" and "result saved", the resumed agent does not pay again
- [ ] When the gateway has no idempotency keys, an unknown outcome is flagged for a person, never retried
- [ ] The audit log shows every attempt, including the one that crashed
- [ ] All 8 checks pass (offline)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend (EXER029).** Refunds above ₱1,000 wait for a supervisor's approval with `interrupt()`. *Done when:* the run pauses, resumes on approval, the tool body visibly runs twice, and the money moves once.
2. **Connect (EXER035).** Write a reconciliation report that compares the ledger with the gateway's refunds. *Done when:* every key is classified as matched, paid but not recorded, recorded but not paid, or an unknown payment, one JSON line each, with a summary.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER043/stretch/goal1_approval_before_commit.py
uv run python EXER043/stretch/goal2_reconciliation.py
```
