"""EXER047 checks. Run:  uv run python EXER047/check.py

Offline. Real SQLite, a real Chroma index and real files in a temporary folder; the embeddings
are fake (deterministic), so no model is called.
"""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from langchain_core.embeddings import DeterministicFakeEmbedding

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("privacy.py")

EMAIL = "ana.reyes@example.com"
QUESTION = f"I'm {EMAIL}, call 0917 555 0142. Card 4111 1111 1111 1111 was charged twice for NC-1042."


def stores(tmp):
    return mod.Stores(Path(tmp), DeterministicFakeEmbedding(size=32))


def fill(s, at=None):
    s.record_turn("ana", "t1", QUESTION, "Flagged NC-1042.", at=at, memory="likes Barako Bold", note="call Friday")
    s.record_turn("ben", "t2", "Is shipping free?", "Free over ₱1,500.", at=at)


@checker.check("luhn_ok() accepts real card numbers and rejects others")
def _():
    assert mod.luhn_ok("4111111111111111") and mod.luhn_ok("5555555555554444") and mod.luhn_ok("378282246310005")
    assert not mod.luhn_ok("4111111111111112") and not mod.luhn_ok("1234567890123")


@checker.check("redact() removes emails, mobile numbers and card numbers, and keeps order numbers and prices")
def _():
    out = mod.redact(QUESTION)
    assert out == "I'm [EMAIL], call [PHONE]. Card [CARD] was charged twice for NC-1042.", out
    assert mod.redact("+63 917-555-0142 or 09175550142") == "[PHONE] or [PHONE]"
    assert mod.redact("Card 4111-1111-1111-1111.") == "Card [CARD]."
    kept = "Tracking 1234567890123 for ₱4,620 on order NC-1042"
    assert mod.redact(kept) == kept, "a number that fails the Luhn check is not a card"


@checker.check("minimize() puts only the allowed profile fields into the prompt")
def _():
    profile = {"loyalty_tier": "Gold", "first_name": "Ana", "email": EMAIL, "phone": "0917 555 0142",
               "birthday": "1990-04-02"}
    assert mod.minimize(profile) == "first_name: Ana, loyalty_tier: Gold"
    assert mod.minimize({"email": EMAIL}) == ""


@checker.check("traces and the index of past turns hold no email, phone or card number")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        s = stores(tmp)
        fill(s)
        assert EMAIL not in s.traces.read_text() and "4111" not in s.traces.read_text()
        assert all(EMAIL not in doc for doc in s.index.get()["documents"])


@checker.check("delete_user() erases the user from every store, with a receipt, and leaves others alone")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        s = stores(tmp)
        fill(s)
        assert len(mod.find_user_data(s, "ana")) == 5
        receipt = mod.delete_user(s, "ana")
        assert receipt == {"sqlite:conversations": 2, "sqlite:memories": 1, "notes file": 1, "vector index": 1,
                           "traces": 1}, receipt
        assert mod.find_user_data(s, "ana", [EMAIL, "NC-1042"]) == []
        assert mod.find_user_data(s, "ben") == ["sqlite:conversations", "vector index", "traces"]
        again = mod.delete_user(s, "ana")
        assert all(v == 0 for v in again.values()), f"deleting twice is safe and removes nothing more: {again}"
        assert "ana" in json.loads(s.tombstones.read_text())


@checker.check("restoring a backup taken before the deletion does not bring the user back")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        s = stores(tmp)
        fill(s)
        backup = s.backup()
        mod.delete_user(s, "ana")
        removed = s.restore(backup)
        assert removed == {"ana": 3}, removed
        assert mod.find_user_data(s, "ana") == []
        assert "sqlite:conversations" in mod.find_user_data(s, "ben"), "the restore must keep everyone else"


@checker.check("purge_expired() removes data older than the retention period, everywhere, and keeps the rest")
def _():
    now = datetime(2026, 11, 15, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory() as tmp:
        s = stores(tmp)
        fill(s, at=now - timedelta(days=100))
        s.record_turn("carla", "t3", "Do you ship to Japan?", "Yes.", at=now - timedelta(days=5))
        removed = mod.purge_expired(s, now, retention_days=90)
        assert removed == {"conversations": 4, "vector index": 2, "traces": 2}, removed
        assert mod.find_user_data(s, "carla") == ["sqlite:conversations", "vector index", "traces"]
        assert "sqlite:conversations" not in mod.find_user_data(s, "ben")


checker.run()
