"""EXER042 stretch goal 2 — conversations that survive a restart, still per user (EXER028).

    uv run python EXER042/stretch/goal2_durable_threads.py

The lesson keeps conversations in InMemorySaver: a restart forgets them, and
two replicas never share them. EXER028 moved them into SQLite. Here the same
checkpointer is shared by every user's assistant, and the namespaced key
("ana/t1") is the SQLite thread id, so the boundary is stored with the data.

The script runs the "service", stops it, and starts it again in a new process. After the "restart" Ana
can still read and continue her thread; Ben still gets 404 for it.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from aicourse.stretch import solution_module

base = solution_module(__file__, "secure_service.py")


class DurableHelpdesks(base.UserHelpdesks):
    """Per-user assistants that share ONE SQLite checkpointer."""

    def __init__(self, db_path: Path) -> None:
        super().__init__()
        self.db_path = db_path
        self.checkpointer = None

    async def _saver(self) -> AsyncSqliteSaver:
        if self.checkpointer is None:
            self.checkpointer = AsyncSqliteSaver(await aiosqlite.connect(str(self.db_path)))
        return self.checkpointer

    async def _assistant(self, principal):
        if principal.user_id not in self.assistants:
            assistant = await super()._assistant(principal)
            from langchain.agents import create_agent

            import assistant as capstone

            assistant.agent = create_agent(assistant.llm, assistant.tools, system_prompt=capstone.SYSTEM_PROMPT,
                                           checkpointer=await self._saver())
        return self.assistants[principal.user_id]

    async def _history(self, key: str):
        # Read straight from the database: no assistant is needed to read a stored thread.
        saved = await (await self._saver()).aget_tuple({"configurable": {"thread_id": key}})
        if saved is None:
            return None
        messages = saved.checkpoint["channel_values"].get("messages", [])
        return [{"role": m.type, "text": m.text} for m in messages if m.type in ("human", "ai") and m.text] or None

    def close(self) -> None:
        if self.checkpointer is not None:
            asyncio.run_coroutine_threadsafe(self.checkpointer.conn.close(), self.loop).result()


def call(helpdesk, tokens, token, method, path, payload=None):
    body = json.dumps(payload).encode() if payload else b""
    status, data, _ = base.route(method, path, {"Authorization": f"Bearer {token}"}, body, helpdesk, tokens)
    return status, data


def before_restart(tmp: Path) -> None:
    tokens = base.TokenStore()
    ana, ben = tokens.issue("ana", "customer"), tokens.issue("ben", "customer")
    (tmp / "tokens.json").write_text(json.dumps({"records": tokens.records(), "ana": ana, "ben": ben}))
    helpdesk = DurableHelpdesks(tmp / "threads.sqlite")
    status, data = call(helpdesk, tokens, ana, "POST", "/ask", {"question": "Hi, my order number is NC-4471.", "thread_id": "t1"})
    print(f"before restart  ana asks         -> {status}: {data['answer'][:70]}")
    helpdesk.close()


def after_restart(tmp: Path) -> None:
    saved = json.loads((tmp / "tokens.json").read_text())
    tokens, ana, ben = base.TokenStore(saved["records"]), saved["ana"], saved["ben"]
    helpdesk = DurableHelpdesks(tmp / "threads.sqlite")
    status, data = call(helpdesk, tokens, ana, "GET", "/threads/t1")
    print(f"after restart   ana reads t1     -> {status}, {len(data.get('messages', []))} messages")
    status, data = call(helpdesk, tokens, ben, "GET", "/threads/t1")
    print(f"after restart   ben reads t1     -> {status} {data}")
    status, data = call(helpdesk, tokens, ana, "POST", "/ask", {"question": "What was my order number?", "thread_id": "t1"})
    print(f"after restart   ana continues t1 -> {status}: {data['answer'][:70]}")
    helpdesk.close()
    assert "4471" in data["answer"], "the conversation should have survived the restart"


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--after-restart":
        base.NOTES_ROOT = Path(sys.argv[2])
        after_restart(Path(sys.argv[2]))
        return
    with tempfile.TemporaryDirectory() as tmp:
        base.NOTES_ROOT = Path(tmp)
        before_restart(Path(tmp))
        sys.stdout.flush()
        # A restart is a new process: nothing in memory survives, only the SQLite file.
        subprocess.run([sys.executable, __file__, "--after-restart", tmp], check=True)


if __name__ == "__main__":
    main()
