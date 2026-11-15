"""EXER048 — Release-Gated Evaluation (starter).

    uv run python EXER048/starter/release_gate.py gate --replay     # deterministic: recorded replies (CI, no secrets)
    uv run python EXER048/starter/release_gate.py gate --live       # the real capstone evaluation (manual, needs .env)
    uv run python EXER048/starter/release_gate.py record            # live: record replies + results for replay
    uv run python EXER048/starter/release_gate.py approve --by <name>   # make the last results the new baseline

"Evaluation is the definition of done" (Lecture 037) only works if nothing
ships without passing it. This lesson turns the capstone evaluation into a
release gate:

1. A RELEASE is identified by what changes answers: the prompt version (a hash
   of the system prompt), the tools, and the model.
2. A BASELINE is the per-category result of an approved release, saved with
   that identity and who approved it.
3. The GATE compares a candidate release with the baseline per category and
   fails on a regression. Safety may never drop.
4. Two modes: REPLAY re-scores recorded replies (deterministic, free, no
   secrets: every pull request) and LIVE runs the real evaluation (manually,
   with secrets, before a release). Both write a Markdown report. Replay
   refuses recordings made for another prompt, tool set or model: a change to
   what the model is asked needs new recordings, made live.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from aicourse.stretch import solution_path

HERE = Path(__file__).resolve().parent.parent
BASELINE = HERE / "baseline.json"
RECORDINGS = HERE / "recordings.json"
REPORT = Path(__file__).resolve().parent / "output" / "release_gate.md"
LAST_RESULTS = Path(__file__).resolve().parent / "output" / "last_results.json"

solution_path(str(HERE.parent / "EXER037" / "solution" / "x.py"))  # the capstone's modules, by name
import assistant as capstone  # noqa: E402
import evaluate  # noqa: E402

Results = dict[str, dict[str, int]]  # {category: {"passed": n, "total": n}}


# ------------------------------------------------------------------ 1. what is being released
def prompt_version(text: str) -> str:
    """A short, stable id for a prompt: "p-" + the first 12 hex digits of its sha256.

    Normalize first: replace "\r\n" with "\n" and strip, so a file saved on Windows gets the same id.
    """
    # TODO
    raise NotImplementedError("prompt_version")


def current_release(model: str) -> dict:
    """The identity of what would ship (given)."""
    import tools as capstone_tools

    tool_text = "\n".join(sorted(f"{t.name}: {t.description}" for t in capstone_tools.LOCAL_TOOLS))
    return {"prompt_version": prompt_version(capstone.SYSTEM_PROMPT),
            "tools_version": prompt_version(tool_text) + "+mcp:notes", "model": model}


def changed(old: dict, new: dict) -> list[str]:
    """The identity fields that differ between two releases."""
    return [key for key in ("prompt_version", "tools_version", "model") if old.get(key) != new.get(key)]


def results_from_rows(rows: list[dict]) -> Results:
    return {c: {"passed": p, "total": t} for c, (p, t) in evaluate.category_scores(rows).items()}


# ------------------------------------------------------------------ 2. the comparison
def compare(baseline: Results, current: Results, tolerance: int = 0) -> list[dict]:
    """One finding per category, over the categories of BOTH results (sorted). A finding is a dict with
    "category", "level" ("fail", "warn" or "ok") and "reason"; when both results have the category, also
    "baseline" and "now" as "passed/total" strings.

    - in the baseline, not in current           -> fail  (cases were dropped)
    - in current, not in the baseline           -> warn  (nothing to compare with)
    - drop = baseline passed - current passed; allowed = 0 for "safety", else tolerance
      drop > allowed                            -> fail
      rate below the capstone's bar             -> fail  (bar: evaluate.CATEGORY_THRESHOLDS.get(category,
                                                                        evaluate.PASS_THRESHOLD))
      0 < drop <= allowed                       -> warn
      otherwise                                 -> ok    (reason "improved" when drop < 0)
    """
    # TODO
    raise NotImplementedError("compare")


def gate(baseline: dict, release: dict, current: Results, tolerance: int = 0) -> tuple[bool, str]:
    """(passed?, Markdown report).

    findings = compare(baseline["results"], current, tolerance); passed = no finding is "fail".
    The report, in this order:
      "# Release gate: PASSED" (or FAILED)
      who approved the baseline and when (baseline["approved_by"], ["approved_at"])
      a table of prompt_version, tools_version and model: baseline vs this release; add " (changed)" after
        a value that differs
      a table with one row per finding: category, baseline, now, ✅ / ⚠️ / ❌, reason
      when it passed AND the release differs from the baseline: a line saying how to approve it
        (`release_gate.py approve --by <your name>`, then commit baseline.json)
    End with a newline.
    """
    # TODO
    raise NotImplementedError("gate")


# ------------------------------------------------------------------ 3. replay: recorded replies, no model (given)
class Recorder:
    """Wraps the real assistant and keeps every reply, keyed by the question."""

    def __init__(self, assistant) -> None:
        self.assistant = assistant
        self.replies: dict[str, dict] = {}

    async def ask(self, question: str, thread_id: str = "default"):
        reply = await self.assistant.ask(question, thread_id)
        self.replies[question] = asdict(reply)
        return reply


class Replayer:
    """Answers every question with the recorded reply. Deterministic, free, and needs no secrets."""

    def __init__(self, replies: dict[str, dict]) -> None:
        self.replies = replies

    async def ask(self, question: str, thread_id: str = "default"):
        if question not in self.replies:
            raise KeyError(f"no recording for {question!r}: run `release_gate.py record` after changing the cases")
        return capstone.Reply(**self.replies[question])


async def run(assistant) -> list[dict]:
    cases = json.loads(evaluate.EVAL_SET.read_text(encoding="utf-8"))
    return await evaluate.run_eval(assistant, cases)


async def live_assistant(tmp: Path):
    import tools as capstone_tools

    tools = capstone_tools.LOCAL_TOOLS + await capstone_tools.load_mcp_tools(tmp / "notes.json")
    return await capstone.Assistant(tools=tools).setup()


# ------------------------------------------------------------------ commands (given)
def model_name() -> str:
    from aicourse.settings import get_settings

    return get_settings().chat_model


def save_results(release: dict, results: Results) -> None:
    LAST_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    LAST_RESULTS.write_text(json.dumps({"release": release, "results": results}, indent=2), encoding="utf-8")


def approve(approver: str, source: Path = LAST_RESULTS, target: Path = BASELINE) -> dict:
    data = json.loads(source.read_text(encoding="utf-8"))
    baseline = {**data, "approved_by": approver, "approved_at": datetime.now(timezone.utc).date().isoformat()}
    target.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    return baseline


async def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "gate"
    if command == "approve":
        approver = sys.argv[sys.argv.index("--by") + 1] if "--by" in sys.argv else "unknown"
        print(json.dumps(approve(approver), indent=2))
        return 0
    if command == "record":
        with tempfile.TemporaryDirectory() as tmp:
            recorder = Recorder(await live_assistant(Path(tmp)))
            rows = await run(recorder)
        release = current_release(model_name())
        RECORDINGS.write_text(json.dumps({"release": release, "replies": recorder.replies}, indent=2,
                                         ensure_ascii=False) + "\n", encoding="utf-8")
        save_results(release, results_from_rows(rows))
        print(f"Recorded {len(recorder.replies)} replies to {RECORDINGS.name}; results in {LAST_RESULTS}")
        return 0

    # gate
    if "--live" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            rows = await run(await live_assistant(Path(tmp)))
        release = current_release(model_name())
    else:
        recorded = json.loads(RECORDINGS.read_text(encoding="utf-8"))
        release = current_release(recorded["release"]["model"])
        stale = changed(recorded["release"], release)
        if stale:  # the code changed what the model is asked, the recordings show the old answers
            print(f"FAILED: {', '.join(stale)} changed since the replies were recorded. Run `release_gate.py record` "
                  "(live) and `gate --live`, and commit the new recordings with the change.")
            return 1
        rows = await run(Replayer(recorded["replies"]))
    current = results_from_rows(rows)
    save_results(release, current)
    passed, report = gate(json.loads(BASELINE.read_text(encoding="utf-8")), release, current)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    print(report)
    print(f"Report: {REPORT}")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
