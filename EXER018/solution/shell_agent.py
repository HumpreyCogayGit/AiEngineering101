"""EXER018 — CLI Calling (reference solution).

Giving a model a shell is the most powerful — and most dangerous — tool.
Defence in depth:
  1. allowlist of programs        4. timeout
  2. no shell operators            5. output truncation
  3. human confirmation            6. a sandbox working directory
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path
from typing import Callable

from langchain.agents import create_agent
from langchain_core.tools import tool

from aicourse.llm import get_chat_model

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"
ALLOWED_COMMANDS = {"ls", "cat", "head", "tail", "wc", "grep", "echo", "pwd", "date", "sort", "uniq", "find"}
FORBIDDEN_TOKENS = [";", "&&", "||", "|", ">", "<", "`", "$(", "\n", "&"]
FORBIDDEN_ARGS = {"-exec", "-execdir", "-delete", "-ok"}  # `find` can run or delete things
MAX_OUTPUT = 2000


def is_allowed(command: str, allowed: set[str] = ALLOWED_COMMANDS) -> tuple[bool, str]:
    """Static checks BEFORE running anything. Returns (ok, reason)."""
    if not command.strip():
        return False, "empty command"
    for token in FORBIDDEN_TOKENS:
        if token in command:
            return False, f"shell operator {token!r} is not allowed"
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return False, f"could not parse command: {exc}"
    program = parts[0]
    if "/" in program or program not in allowed:
        return False, f"program {program!r} is not in the allowlist"
    if any(arg in FORBIDDEN_ARGS for arg in parts[1:]):
        return False, "forbidden argument"
    if any(arg.startswith("/") or ".." in arg for arg in parts[1:]):
        return False, "paths outside the workspace are not allowed"
    return True, "ok"


def truncate(text: str, limit: int = MAX_OUTPUT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} characters]"


def run_command(
    command: str,
    confirm: Callable[[str], bool] = lambda c: True,
    allowed: set[str] = ALLOWED_COMMANDS,
    timeout: float = 10,
    cwd: Path = WORKSPACE,
) -> str:
    ok, reason = is_allowed(command, allowed)
    if not ok:
        return f"REFUSED: {reason}"
    if not confirm(command):
        return "DENIED: the user did not approve this command"
    try:
        result = subprocess.run(
            shlex.split(command),          # a list, and shell=False (the default): no shell parsing
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: command timed out after {timeout}s"
    output = result.stdout + (f"\n[stderr]\n{result.stderr}" if result.stderr else "")
    return truncate(f"[exit code {result.returncode}]\n{output}")


def ask_user(command: str) -> bool:
    answer = input(f"\n  The agent wants to run: {command}\n  Allow? [y/N] ").strip().lower()
    return answer in ("y", "yes")


def make_shell_tool(confirm: Callable[[str], bool] = ask_user):
    @tool
    def shell(command: str) -> str:
        """Run a read-only shell command inside the project workspace folder.
        Allowed programs: ls, cat, head, tail, wc, grep, echo, pwd, date, sort, uniq, find.
        Pipes, redirects and command chaining are NOT allowed — run one command at a time."""
        return run_command(command, confirm=confirm)

    return shell


def build_agent(confirm: Callable[[str], bool] = ask_user):
    return create_agent(
        get_chat_model(temperature=0),
        [make_shell_tool(confirm)],
        system_prompt="You help users explore files in a workspace using the shell tool. "
                      "Run one simple command at a time and explain what you found.",
    )


def main() -> None:
    agent = build_agent()
    print(f"Shell agent. Workspace: {WORKSPACE}\nType /exit to quit.")
    while True:
        try:
            q = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q == "/exit":
            break
        if q:
            result = agent.invoke({"messages": [("user", q)]})
            print("Agent:", result["messages"][-1].text)


if __name__ == "__main__":
    main()
