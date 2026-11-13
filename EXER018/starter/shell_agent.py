"""EXER018 — CLI Calling.

Giving a model a shell is the most powerful — and most dangerous — tool.
Defence in depth:
  1. allowlist of programs        4. timeout
  2. no shell operators            5. output truncation
  3. human confirmation            6. a sandbox working directory

    uv run python EXER018/starter/shell_agent.py
    uv run python EXER018/check.py
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
    """Static checks BEFORE running anything. Return (ok, reason).

    Reject (return False, "<reason>") when:
      - the command is empty / whitespace
      - it contains any FORBIDDEN_TOKENS
      - shlex.split(command) fails (catch ValueError)
      - the program (first word) contains "/" or is not in `allowed`
      - any argument is in FORBIDDEN_ARGS
      - any argument starts with "/" or contains ".." (escaping the workspace)
    Otherwise return (True, "ok").
    """
    # TODO
    raise NotImplementedError("is_allowed")


def truncate(text: str, limit: int = MAX_OUTPUT) -> str:
    """Return text unchanged if short enough, else the first `limit` characters
    followed by "\n... [truncated N characters]"."""
    # TODO
    raise NotImplementedError("truncate")


def run_command(
    command: str,
    confirm: Callable[[str], bool] = lambda c: True,
    allowed: set[str] = ALLOWED_COMMANDS,
    timeout: float = 10,
    cwd: Path = WORKSPACE,
) -> str:
    """Run a command safely and return text for the model.

    1. ok, reason = is_allowed(command, allowed); if not ok: return f"REFUSED: {reason}"
    2. if not confirm(command): return "DENIED: the user did not approve this command"
    3. subprocess.run(shlex.split(command), cwd=cwd, capture_output=True, text=True, timeout=timeout)
       NEVER use shell=True.
       On subprocess.TimeoutExpired return "ERROR: command timed out after <timeout>s"
    4. return truncate(f"[exit code N]\n<stdout>") (+ stderr if any)
    """
    # TODO
    raise NotImplementedError("run_command")


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
