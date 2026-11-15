"""EXER043 stretch goal 2 — a reconciliation report: does our ledger agree with the gateway? (EXER035)

    uv run python EXER043/stretch/goal2_reconciliation.py      # offline: simulated day of refunds

Idempotency keys stop double payments. They cannot tell you about the cases
where the two records disagree, which is what a nightly reconciliation is for.
It compares our ledger with the provider's list of refunds and sorts every key
into one of four outcomes:

    matched            done in the ledger, paid at the gateway, same refund id
    paid, not recorded the gateway paid, the ledger says pending: finish the row
    recorded, not paid pending or needs_review, nothing at the gateway: safe to retry or cancel
    unknown payment    the gateway paid a key the ledger has never seen: alert a person

The report is one JSON line per finding (EXER035: logs a machine can read) plus a summary.
"""

from __future__ import annotations

import json

from aicourse.stretch import solution_module

base = solution_module(__file__, "refunds.py")


def gateway_refunds(gateway) -> dict[str, dict]:
    """What the provider says it paid, by idempotency key (real APIs let you list or search refunds)."""
    by_id = {m["refund_id"]: m for m in gateway.money_moved}
    return {key: by_id[refund_id] for key, refund_id in gateway._by_key.items()}


def reconcile(ledger, paid: dict[str, dict]) -> list[dict]:
    names = ("key", "order_id", "amount", "status", "refund_id")
    rows = {r[0]: dict(zip(names, r)) for r in ledger.db.execute(f"SELECT {', '.join(names)} FROM refunds")}
    findings = []
    for key, row in rows.items():
        at_gateway = paid.get(key)
        if row["status"] == "done" and at_gateway and at_gateway["refund_id"] == row["refund_id"]:
            outcome = "matched"
        elif at_gateway:
            outcome = "paid, not recorded"
        else:
            outcome = "recorded, not paid"
        findings.append({"key": key, "order_id": row["order_id"], "amount": row["amount"],
                         "ledger": row["status"], "outcome": outcome})
    for key, payment in paid.items():
        if key not in rows:
            findings.append({"key": key, "order_id": payment["order_id"], "amount": payment["amount"],
                             "ledger": None, "outcome": "unknown payment"})
    return findings


def simulate_day():
    ledger, gateway = base.Ledger(), base.PaymentGateway()
    base.issue_refund(ledger, gateway, "refund:t1:c1", "NC-1042", 3450, "agent:t1")      # normal
    base.issue_refund(ledger, gateway, "refund:t2:c1", "NC-1043", 300, "agent:t2")       # normal
    gateway.crash_after_next_refund = True                                               # paid, then died
    try:
        base.issue_refund(ledger, gateway, "refund:t3:c1", "NC-1043", 200, "agent:t3")
    except base.SimulatedCrash:
        pass
    ledger.begin("refund:t4:c1", "NC-1044", 390)                                         # died before paying
    gateway.refund("NC-1044", 100, idempotency_key="manual:ops:42")                      # paid outside the agent
    return ledger, gateway


def main() -> None:
    ledger, gateway = simulate_day()
    findings = reconcile(ledger, gateway_refunds(gateway))
    for finding in findings:
        print(json.dumps(finding, ensure_ascii=False))
    summary = {}
    for finding in findings:
        summary[finding["outcome"]] = summary.get(finding["outcome"], 0) + 1
    print("\nsummary:", json.dumps(summary))
    print("Only 'matched' needs nothing. Every other line is a task for a person or a repair job.")


if __name__ == "__main__":
    main()
