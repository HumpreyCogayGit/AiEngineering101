"""EXER029 stretch goal 2 — close the script, resume the approval later (EXER028).

    uv run python EXER029/stretch/goal2_resume_later.py start       # runs until the agent needs approval, then EXITS
    uv run python EXER029/stretch/goal2_resume_later.py status      # a new process: what is waiting?
    uv run python EXER029/stretch/goal2_resume_later.py approve     # a new process: continue the same run
    uv run python EXER029/stretch/goal2_resume_later.py reject "not today"

With InMemorySaver a paused run dies with the process. With the SQLite
checkpointer from EXER028 the pause is a row in a file: the approver can
answer tomorrow, from another program. Nothing else changes: the same graph,
the same thread_id, `Command(resume=...)`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "hitl_agent.py")
memory = solution_module(__file__, "memory_bot.py", exercise="EXER028")

DB = Path(__file__).resolve().parent / "output" / "approvals.sqlite"
THREAD = "support-inbox"


def open_graph():
    return base.build_graph(get_chat_model(temperature=0), checkpointer=memory.sqlite_checkpointer(DB))


def waiting(graph) -> dict | None:
    """The pending approval of the saved thread, read from the checkpoint (no model call)."""
    state = graph.get_state(base.config_for(THREAD))
    return state.interrupts[0].value if state.interrupts else None


def show(payload: dict | None) -> None:
    if payload is None:
        print("Nothing is waiting for approval.")
        return
    print("Waiting for approval:")
    for call in payload["tool_calls"]:
        print(f"  {call['name']}({call['args']})"[:200])


def report(result: dict) -> None:
    if (payload := base.pending(result)) is not None:
        show(payload)
        print("\nThe process ends here. Run `approve` or `reject` whenever you like.")
    else:
        print("Agent:", result["messages"][-1].text[:300])
        print(f"Emails sent by this process: {len(base.OUTBOX)}; refunds: {len(base.REFUNDS)}")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "status"
    if command == "start":
        DB.unlink(missing_ok=True)  # a fresh run for the demo
        report(base.start(open_graph(), "Please handle the inbox.", THREAD))
    elif command == "status":
        show(waiting(open_graph()))
    elif command in ("approve", "reject"):
        graph = open_graph()
        if waiting(graph) is None:
            print("Nothing is waiting for approval. Run `start` first.")
            return
        decision = {"action": "approve"} if command == "approve" else {
            "action": "reject", "reason": sys.argv[2] if len(sys.argv) > 2 else "no reason given"}
        report(base.resume(graph, THREAD, decision))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
