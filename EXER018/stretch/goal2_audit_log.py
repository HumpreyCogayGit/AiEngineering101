"""EXER018 stretch goal 2 — an audit log of every command.

    uv run python EXER018/stretch/goal2_audit_log.py       # offline

Every command the model proposes is written to a JSONL file: one JSON object
per line with the time, the command, the decision and the exit code. JSONL
is append-only and survives a crash mid-run, which is what you want from a
log. Refused and denied commands are logged too: they are the interesting ones.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from aicourse.stretch import solution_module

base = solution_module(__file__, "shell_agent.py")

AUDIT_FILE = Path(__file__).resolve().parent / "output" / "audit.jsonl"


def classify(result: str) -> tuple[str, int | None]:
    """Turn run_command's result text into (decision, exit code)."""
    if result.startswith("REFUSED"):
        return "refused", None
    if result.startswith("DENIED"):
        return "denied", None
    if result.startswith("ERROR"):
        return "timeout", None
    match = re.match(r"\[exit code (-?\d+)\]", result)
    return "ran", int(match.group(1)) if match else None


def audited_run(command: str, confirm: Callable[[str], bool] = lambda c: True,
                audit_file: Path = AUDIT_FILE, **kwargs) -> str:
    """run_command, plus one line in the audit log. The result is returned unchanged."""
    result = base.run_command(command, confirm=confirm, **kwargs)
    decision, exit_code = classify(result)
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": command,
        "decision": decision,
        "exit_code": exit_code,
        # Why it was stopped, or how much came back. Never the output itself: it may hold private data.
        "detail": result.split("\n", 1)[0] if decision != "ran" else f"{len(result)} characters of output",
    }
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with audit_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return result


def main() -> None:
    AUDIT_FILE.unlink(missing_ok=True)  # a fresh log for the demo
    never_grep = lambda command: not command.startswith("grep")  # a "user" who denies grep
    for command in ["ls", "wc -l sales.csv", "cat missing.txt", "grep 2026-03 sales.csv",
                    "cat notes.txt; rm -rf ~", "find . -delete"]:
        audited_run(command, confirm=never_grep)

    print(f"{AUDIT_FILE.relative_to(AUDIT_FILE.parents[3])}:")
    for line in AUDIT_FILE.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        print(f"  {entry['decision']:<8} exit={str(entry['exit_code']):<5} {entry['command']:<28} {entry['detail']}")
    print("\nTo audit an agent, pass audited_run as the tool's runner instead of run_command.")


if __name__ == "__main__":
    main()
