"""EXER047 stretch goal 1 — answer a data access request: everything we hold about one person.

    uv run python EXER047/stretch/goal1_access_request.py      # offline

Privacy laws give people a right to see their data as well as to erase it (the
Philippine Data Privacy Act, the GDPR and others). The same inventory that
deletion needs answers it: every store, searched for one user id. The export
is for the person themselves, so it is NOT redacted, and it is written as JSON
a machine can read, with the time it was made and the stores it covered.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from langchain_core.embeddings import DeterministicFakeEmbedding

from aicourse.stretch import solution_module

base = solution_module(__file__, "privacy.py")


def export_user(stores, user_id: str) -> dict:
    def rows(sql: str) -> list[dict]:
        cursor = stores.db.execute(sql, (user_id,))
        names = [column[0] for column in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]

    notes = stores.notes_file(user_id)
    index = stores.index.get(where={"user_id": user_id})
    traces = [json.loads(line) for line in stores.traces.read_text(encoding="utf-8").splitlines()
              if line.strip() and json.loads(line)["user_id"] == user_id] if stores.traces.exists() else []
    tombstones = json.loads(stores.tombstones.read_text()) if stores.tombstones.exists() else {}
    return {
        "user_id": user_id,
        "exported_at": base.now_utc().isoformat(),
        "deleted_at": tombstones.get(user_id),
        "conversations": rows("SELECT thread_id, role, text, at FROM conversations WHERE user_id = ? ORDER BY at"),
        "memories": rows("SELECT fact, at FROM memories WHERE user_id = ?"),
        "notes": json.loads(notes.read_text()) if notes.exists() else [],
        "indexed_past_turns": index["documents"],
        "traces": traces,
        "stores_covered": ["sqlite:conversations", "sqlite:memories", "notes file", "vector index", "traces"],
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        stores = base.Stores(Path(tmp), DeterministicFakeEmbedding(size=32))
        stores.record_turn("ana", "t1", "I'm ana.reyes@example.com. When do my stars expire?", "After 12 months.",
                           memory="Gold member", note="birthday in April", tokens=800)
        stores.record_turn("ana", "t2", "Is the BGC café pet friendly?", "Yes, at the outdoor tables.", tokens=600)
        stores.record_turn("ben", "t3", "Is shipping free?", "Free over ₱1,500.", tokens=500)
        export = export_user(stores, "ana")
        print(json.dumps(export, indent=2, ensure_ascii=False))
        assert all(t["user_id"] == "ana" for t in export["traces"]) and len(export["conversations"]) == 4
        print(f"\n... {len(export['conversations'])} conversation rows, {len(export['traces'])} traces; nothing of ben's.")


if __name__ == "__main__":
    main()
