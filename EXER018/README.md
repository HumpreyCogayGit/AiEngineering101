# EXER018 — CLI Calling

**Module 3 · Tool Calling** · Lecture: [Lecture/lectures/lec018.html](../Lecture/lectures/lec018.html)

## Goal

Let an LLM run shell commands safely. Learn why a shell tool is one of the
riskiest tools you can give a model, and build several independent layers of defence.

## The project

A file-explorer agent that answers questions about the files in
[workspace/](workspace/) by running commands like `ls`, `cat`, `grep` and `wc`.

## Tasks

Complete the TODOs in `starter/shell_agent.py`:

1. `is_allowed`: allowlist, forbidden shell operators, forbidden arguments, path escapes
2. `truncate`: never flood the context window with output
3. `run_command`: confirmation, `subprocess.run` with a list and **no** `shell=True`, timeout

## Run it

```bash
uv run python EXER018/starter/shell_agent.py
uv run python EXER018/check.py
```

Try: "Which branch sold the most cups in March?", "What's on my todo list?",
and "Delete all the files" (it should not be able to).

## Success criteria

- [ ] All 15 dangerous commands in `check.py` are refused
- [ ] You are asked to approve every command before it runs
- [ ] The agent answers questions about the workspace files correctly
- [ ] All 6 checks pass

## Stretch goals

Optional. Neither goal is needed to complete the exercise, and `check.py` must still pass when you are done.

1. **Extend.** Add a dry-run mode that explains each command instead of running it. *Done when:* every command prints what it would do or why it would be refused, and nothing is executed.
2. **Connect (EXER035).** Log every command, the decision and the exit code to a JSONL audit file. *Done when:* the file has one line per command, including the refused and denied ones.

Reference code, for after you have tried (it builds on `solution/` and changes nothing in it):

```bash
uv run python EXER018/stretch/goal1_dry_run.py
uv run python EXER018/stretch/goal2_audit_log.py
```
