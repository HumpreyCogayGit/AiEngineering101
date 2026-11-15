"""EXER047 — Privacy and Data Lifecycle (reference solution).

    uv run python EXER047/solution/privacy.py        # record a user's data everywhere, delete it, prove it is gone

A helpdesk that remembers people keeps personal data in more places than
anyone remembers: conversation history, long-term memory, notes, a vector
index of past turns, traces, and the backups of all of them. This lesson
handles that data through its whole life:

1. MINIMIZE   send the model only the profile fields the task needs
2. REDACT     never write emails, phone numbers or card numbers into traces
3. RETAIN     delete traces and conversations when their retention period ends
4. DELETE     erase one user everywhere, with a receipt that says what was removed
5. RESTORE    a restored backup must not bring a deleted user back: tombstones
"""

from __future__ import annotations

import json
import re
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

ALLOWED_PROFILE_FIELDS = ("first_name", "loyalty_tier")  # all the helpdesk needs to greet and answer

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(\.[\w-]+)+\b")
PHONE = re.compile(r"(?<!\w)(\+63[\s-]?|0)9\d{2}[\s-]?\d{3}[\s-]?\d{4}(?!\d)")   # Philippine mobile numbers
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")                          # 13 to 19 digits, spaces or dashes


# ------------------------------------------------------------------ 1 + 2. minimize and redact
def luhn_ok(digits: str) -> bool:
    """The Luhn checksum that every payment card number satisfies."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        n = int(ch)
        if i % 2 == 1:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


def redact(text: str) -> str:
    """Replace emails, mobile numbers and card numbers with placeholders. Order numbers stay."""
    text = EMAIL.sub("[EMAIL]", text)
    text = PHONE.sub("[PHONE]", text)

    def card(match: re.Match) -> str:
        digits = re.sub(r"\D", "", match.group())
        return "[CARD]" if 13 <= len(digits) <= 19 and luhn_ok(digits) else match.group()

    return CARD.sub(card, text)


def minimize(profile: dict) -> str:
    """The customer context for the prompt: allowed fields only, in a fixed order."""
    return ", ".join(f"{k}: {profile[k]}" for k in ALLOWED_PROFILE_FIELDS if profile.get(k))


# ------------------------------------------------------------------ the stores (given)
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Stores:
    """Every place the helpdesk keeps data about a person, in one folder."""
    root: Path
    embeddings: object

    def __post_init__(self) -> None:
        import chromadb
        from langchain_chroma import Chroma

        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "notes").mkdir(exist_ok=True)
        (self.root / "backups").mkdir(exist_ok=True)
        self.db = sqlite3.connect(str(self.root / "helpdesk.sqlite"))
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (user_id TEXT, thread_id TEXT, role TEXT, text TEXT, at TEXT);
            CREATE TABLE IF NOT EXISTS memories (user_id TEXT, fact TEXT, at TEXT);""")
        client = chromadb.PersistentClient(path=str(self.root / "index"),
                                           settings=chromadb.Settings(anonymized_telemetry=False))
        self.index = Chroma(client=client, collection_name="past_turns", embedding_function=self.embeddings,
                            collection_metadata={"hnsw:space": "cosine"})

    @property
    def traces(self) -> Path:
        return self.root / "traces.jsonl"

    @property
    def tombstones(self) -> Path:
        # NOT inside the database: restoring an old database must not restore the deletions away.
        return self.root / "tombstones.json"

    def notes_file(self, user_id: str) -> Path:
        return self.root / "notes" / f"{user_id}.json"

    def record_turn(self, user_id: str, thread_id: str, question: str, answer: str, at: datetime | None = None,
                    memory: str | None = None, note: str | None = None, tokens: int = 0) -> None:
        """What a helpdesk turn leaves behind, in every store.

        The conversation keeps the user's own words (they can read their history). Everything
        derived from it (the index of past turns, the traces) is redacted: retrieval and debugging
        need the meaning of a question, not the customer's phone number."""
        at_text = (at or now_utc()).isoformat()
        self.db.executemany("INSERT INTO conversations VALUES (?, ?, ?, ?, ?)",
                            [(user_id, thread_id, "user", question, at_text),
                             (user_id, thread_id, "assistant", answer, at_text)])
        if memory:
            self.db.execute("INSERT INTO memories VALUES (?, ?, ?)", (user_id, memory, at_text))
        self.db.commit()
        if note:
            path = self.notes_file(user_id)
            notes = json.loads(path.read_text()) if path.exists() else []
            path.write_text(json.dumps(notes + [note]))
        self.index.add_texts([redact(f"Q: {question}\nA: {answer}")], metadatas=[{"user_id": user_id, "at": at_text}])
        with self.traces.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": at_text, "user_id": user_id, "question": redact(question),
                                "tokens": tokens}) + "\n")

    def backup(self) -> Path:
        target = self.root / "backups" / f"helpdesk-{now_utc().strftime('%Y%m%dT%H%M%S%f')}.sqlite"
        self.db.commit()
        with sqlite3.connect(str(target)) as copy:
            self.db.backup(copy)
        return target

    def restore(self, backup: Path) -> dict:
        """Put an old copy of the database back, then re-apply every deletion made since."""
        self.db.close()
        shutil.copyfile(backup, self.root / "helpdesk.sqlite")
        self.db = sqlite3.connect(str(self.root / "helpdesk.sqlite"))
        return apply_tombstones(self)


def find_user_data(stores: Stores, user_id: str, needles: list[str] = ()) -> list[str]:
    """Every place where the user id, or any of the given strings, still appears."""
    found = []
    for table in ("conversations", "memories"):
        if stores.db.execute(f"SELECT 1 FROM {table} WHERE user_id = ? LIMIT 1", (user_id,)).fetchone():
            found.append(f"sqlite:{table}")
    if stores.notes_file(user_id).exists():
        found.append("notes file")
    if stores.index.get(where={"user_id": user_id})["ids"]:
        found.append("vector index")
    if stores.traces.exists():
        text = stores.traces.read_text(encoding="utf-8")
        if f'"user_id": "{user_id}"' in text or any(n in text for n in needles):
            found.append("traces")
    return found


# ------------------------------------------------------------------ 3. retention
def purge_expired(stores: Stores, now: datetime, retention_days: int) -> dict:
    """Delete conversations, vector entries and trace lines older than the retention period."""
    cutoff = (now - timedelta(days=retention_days)).isoformat()
    removed = {"conversations": stores.db.execute("DELETE FROM conversations WHERE at < ?", (cutoff,)).rowcount}
    stores.db.commit()
    entries = stores.index.get()
    old = [i for i, meta in zip(entries["ids"], entries["metadatas"]) if meta["at"] < cutoff]
    if old:
        stores.index.delete(ids=old)
    removed["vector index"] = len(old)
    removed["traces"] = _rewrite_traces(stores, lambda entry: entry["at"] >= cutoff)
    return removed


def _rewrite_traces(stores: Stores, keep) -> int:
    """Keep the trace lines for which keep(entry) is true; return how many were removed (given)."""
    if not stores.traces.exists():
        return 0
    entries = [json.loads(line) for line in stores.traces.read_text(encoding="utf-8").splitlines() if line.strip()]
    kept = [e for e in entries if keep(e)]
    stores.traces.write_text("".join(json.dumps(e) + "\n" for e in kept), encoding="utf-8")
    return len(entries) - len(kept)


# ------------------------------------------------------------------ 4. deletion, everywhere
def delete_user(stores: Stores, user_id: str) -> dict:
    """Erase one user from every store. Returns a receipt: how much was removed from each.
    Safe to run twice; the tombstone makes it survive a restore."""
    receipt = {}
    for table in ("conversations", "memories"):
        receipt[f"sqlite:{table}"] = stores.db.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,)).rowcount
    stores.db.commit()
    notes = stores.notes_file(user_id)
    receipt["notes file"] = int(notes.exists())
    notes.unlink(missing_ok=True)
    ids = stores.index.get(where={"user_id": user_id})["ids"]
    if ids:
        stores.index.delete(ids=ids)
    receipt["vector index"] = len(ids)
    receipt["traces"] = _rewrite_traces(stores, lambda entry: entry["user_id"] != user_id)
    tombstones = json.loads(stores.tombstones.read_text()) if stores.tombstones.exists() else {}
    tombstones.setdefault(user_id, now_utc().isoformat())
    stores.tombstones.write_text(json.dumps(tombstones, indent=2))
    return receipt


# ------------------------------------------------------------------ 5. restores respect deletions
def apply_tombstones(stores: Stores) -> dict:
    """Delete again every user deleted since the backup. {user_id: rows removed from the database}."""
    if not stores.tombstones.exists():
        return {}
    removed = {}
    for user_id in json.loads(stores.tombstones.read_text()):
        removed[user_id] = sum(stores.db.execute(f"DELETE FROM {t} WHERE user_id = ?", (user_id,)).rowcount
                               for t in ("conversations", "memories"))
    stores.db.commit()
    return removed


# ------------------------------------------------------------------ demo (given)
def main() -> None:
    import tempfile

    from langchain_core.embeddings import DeterministicFakeEmbedding

    with tempfile.TemporaryDirectory() as tmp:
        stores = Stores(Path(tmp), DeterministicFakeEmbedding(size=64))
        profile = {"first_name": "Ana", "loyalty_tier": "Gold", "email": "ana.reyes@example.com",
                   "phone": "0917 555 0142", "address": "12 Maginhawa St"}
        print(f"Profile in the prompt: {minimize(profile)!r}  (no email, phone or address)\n")
        question = "Hi, I'm ana.reyes@example.com, 0917 555 0142. Card 4111 1111 1111 1111 was charged twice for NC-1042."
        stores.record_turn("ana", "t1", question, "Sorry Ana! I've flagged NC-1042 for a refund.",
                           memory="prefers Barako Bold", note="call back Friday", tokens=900)
        stores.record_turn("ben", "t9", "Is shipping free?", "Free over ₱1,500.", tokens=700)
        print("trace line:", stores.traces.read_text().splitlines()[0])
        backup = stores.backup()

        print("\nbefore deletion, ana appears in:", find_user_data(stores, "ana", ["ana.reyes@example.com"]))
        print("deletion receipt:", delete_user(stores, "ana"))
        print("after deletion, ana appears in:  ", find_user_data(stores, "ana", ["ana.reyes@example.com"]))
        print("ben is untouched:                 ", find_user_data(stores, "ben"))

        print("\nrestoring yesterday's backup ... re-applied deletions:", stores.restore(backup))
        print("after restore, ana appears in:   ", find_user_data(stores, "ana"))


if __name__ == "__main__":
    main()
