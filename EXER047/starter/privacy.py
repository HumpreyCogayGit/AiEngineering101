"""EXER047 — Privacy and Data Lifecycle (starter).

    uv run python EXER047/starter/privacy.py        # record a user's data everywhere, delete it, prove it is gone

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
    """The Luhn checksum that every payment card number satisfies.

    Walk the digits from the RIGHT. Double every second digit (positions 1, 3, 5, ... counting from 0);
    when a doubled digit is above 9, subtract 9. Sum everything. Valid when the sum % 10 == 0.
    "4111111111111111" is valid; "4111111111111112" is not.
    """
    # TODO
    raise NotImplementedError("luhn_ok")


def redact(text: str) -> str:
    """Replace emails with [EMAIL], mobile numbers with [PHONE], card numbers with [CARD].

    Use the patterns EMAIL, PHONE and CARD above, in that order (re.sub).
    CARD matches ANY 13-19 digit run, so pass a function to CARD.sub: strip the spaces and dashes, and
    return "[CARD]" only when luhn_ok(digits) is true; otherwise return match.group() unchanged.
    Order numbers (NC-1042), prices and tracking numbers must survive.
    """
    # TODO
    raise NotImplementedError("redact")


def minimize(profile: dict) -> str:
    """The customer context for the prompt: ", ".join(f"{k}: {profile[k]}") for each k in
    ALLOWED_PROFILE_FIELDS (that order) that has a value. Nothing else from the profile, ever.
    """
    # TODO
    raise NotImplementedError("minimize")


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
    """Delete what is older than the retention period, in every store that keeps history.

    cutoff = (now - timedelta(days=retention_days)).isoformat()   (ISO strings compare like dates)
    - conversations: DELETE ... WHERE at < ?; count = cursor.rowcount; commit
    - vector index:  entries = stores.index.get(); the ids whose metadata["at"] < cutoff; stores.index.delete(ids=...)
    - traces:        _rewrite_traces(stores, keep=lambda entry: entry["at"] >= cutoff)
    Return {"conversations": n, "vector index": n, "traces": n}.
    """
    # TODO
    raise NotImplementedError("purge_expired")


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
    """Erase one user from every store. Return a receipt {store: how much was removed}.

    - "sqlite:conversations", "sqlite:memories": DELETE ... WHERE user_id = ?  (rowcount); commit
    - "notes file": 1 if stores.notes_file(user_id) existed, then unlink it (missing_ok=True)
    - "vector index": ids = stores.index.get(where={"user_id": user_id})["ids"]; delete them if any
    - "traces": _rewrite_traces(stores, lambda entry: entry["user_id"] != user_id)
    Then the tombstone: load stores.tombstones (a JSON object, {} if missing), setdefault(user_id,
    now_utc().isoformat()), and write it back. Running it twice must be safe.
    """
    # TODO
    raise NotImplementedError("delete_user")


# ------------------------------------------------------------------ 5. restores respect deletions
def apply_tombstones(stores: Stores) -> dict:
    """After a restore: delete again every user in the tombstone file.

    Return {user_id: rows removed from conversations + memories}. No tombstone file -> {}.
    The tombstone file lives OUTSIDE the database on purpose: restoring the database cannot undo it.
    """
    # TODO
    raise NotImplementedError("apply_tombstones")


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
