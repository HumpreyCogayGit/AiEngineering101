"""EXER018 stretch goal 1 — a dry-run mode.

    uv run python EXER018/stretch/goal1_dry_run.py            # offline: explains a list of commands
    uv run python EXER018/stretch/goal1_dry_run.py --agent    # live: the agent plans, nothing runs

In dry-run mode every command goes through the same static checks, then is
EXPLAINED instead of executed. You see what an agent would do before you let
it do anything, which is how you build trust in an allowlist.
"""

from __future__ import annotations

import shlex
import sys

from langchain.agents import create_agent
from langchain_core.tools import tool

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "shell_agent.py")

WHAT_IT_DOES = {
    "ls": "lists the files in a folder", "cat": "prints a whole file", "head": "prints the first lines of a file",
    "tail": "prints the last lines of a file", "wc": "counts lines, words and characters",
    "grep": "prints the lines that match a pattern", "echo": "prints its arguments", "pwd": "prints the current folder",
    "date": "prints the current date and time", "sort": "prints the lines in sorted order",
    "uniq": "removes repeated adjacent lines", "find": "lists files that match a condition",
}
assert set(WHAT_IT_DOES) == base.ALLOWED_COMMANDS, "explain every allowed program, and only those"


def explain(command: str) -> str:
    """Same checks as a real run, then a description instead of an execution."""
    ok, reason = base.is_allowed(command)
    if not ok:
        return f"DRY RUN: would be REFUSED ({reason})"
    program, *args = shlex.split(command)
    target = f" with arguments {args}" if args else ""
    return (f"DRY RUN: would run `{program}`{target} in {base.WORKSPACE.name}/ "
            f"({program} {WHAT_IT_DOES[program]}). Nothing was executed.")


def run_command(command: str, dry_run: bool = False, **kwargs) -> str:
    return explain(command) if dry_run else base.run_command(command, **kwargs)


def build_dry_run_agent():
    @tool
    def shell(command: str) -> str:
        """Run a read-only shell command inside the project workspace folder.
        Allowed programs: ls, cat, head, tail, wc, grep, echo, pwd, date, sort, uniq, find.
        Pipes, redirects and command chaining are NOT allowed — run one command at a time."""
        result = run_command(command, dry_run=True)
        print(f"  {command!r}\n    -> {result}")
        return result

    return create_agent(
        get_chat_model(temperature=0), [shell],
        system_prompt="You help users explore files in a workspace using the shell tool. This is a DRY RUN: "
                      "the tool only describes what each command would do. Propose the commands you would "
                      "run, then say what you would look for in their output. Do not invent file contents.",
    )


def main() -> None:
    if "--agent" in sys.argv:
        result = build_dry_run_agent().invoke(
            {"messages": [("user", "Which branch sold the most cups in March?")]})
        print("\nAgent:", result["messages"][-1].text)
        return
    for command in ["ls -la", "grep 2026-03 sales.csv", "cat notes.txt; rm -rf ~", "find . -delete",
                    "python -c 'print(1)'", "cat ../../.env"]:
        print(f"{command}\n  {explain(command)}")


if __name__ == "__main__":
    main()
