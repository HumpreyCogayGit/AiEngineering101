# EXER047 — Privacy and Data Lifecycle

**Module 9 · Running in Production** · Lecture: [Lecture/lectures/lec047.html](../Lecture/lectures/lec047.html)

## Goal

Handle personal data through its whole life: send the model only what it needs, keep it out of traces,
delete it when its retention period ends, erase one person everywhere on request, and make sure a
restored backup does not bring them back.

## The project

| File | Status | Your work |
|---|---|---|
| `privacy.py` | TODO | `luhn_ok`, `redact`, `minimize`, `purge_expired`, `delete_user`, `apply_tombstones` |

Given: `Stores`, the five places the helpdesk keeps data about a person (conversations and long-term
memories in SQLite, a notes file per user, a Chroma index of past turns, a trace log), with
`record_turn`, `backup`, `restore` and `find_user_data`.

## Run it

```bash
uv run python EXER047/starter/privacy.py     # offline: record, delete, restore, and look for what is left
uv run python EXER047/check.py
```

## Success criteria

- [ ] Emails, mobile numbers and card numbers (checked with Luhn) are redacted; order numbers and prices are not
- [ ] Only the allowed profile fields reach the prompt
- [ ] Traces and the index of past turns never hold an email, phone or card number
- [ ] Deleting a user removes them from all five stores, returns a receipt, leaves other users alone, and is safe to repeat
- [ ] Restoring a backup taken before the deletion does not bring the user back
- [ ] Data older than the retention period is removed from conversations, the index and the traces
- [ ] All 7 checks pass (offline)

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Answer a data access request: export everything held about one user as JSON. *Done when:* the export covers every store, says when it was made, and contains nothing about other users.
2. **Connect (EXER035).** Make the EXER035 tracker redact what it stores. *Done when:* for a live question containing a phone number and an email, the original tracker's tool span shows them and the redacting tracker's does not.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER047/stretch/goal1_access_request.py
uv run python EXER047/stretch/goal2_redacting_tracker.py
```
