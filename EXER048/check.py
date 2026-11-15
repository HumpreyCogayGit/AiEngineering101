"""EXER048 checks. Run:  uv run python EXER048/check.py

Offline. The gate is tested with made-up results; the replay runs the real capstone scoring on
the recorded replies; the workflow is read as YAML.
"""

import asyncio
import json
import tempfile
from pathlib import Path

import yaml

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("release_gate.py")

BASE = {"grounding": {"passed": 6, "total": 6}, "arithmetic": {"passed": 4, "total": 4},
        "safety": {"passed": 4, "total": 4}, "memory": {"passed": 3, "total": 4}}
RELEASE = {"prompt_version": "p-aaa", "tools_version": "p-bbb", "model": "m"}


def with_(**changes):
    out = json.loads(json.dumps(BASE))
    for category, passed in changes.items():
        if passed is None:
            out.pop(category)
        elif category in out:
            out[category]["passed"] = passed
        else:
            out[category] = {"passed": passed, "total": 4}
    return out


def levels(findings):
    return {f["category"]: f["level"] for f in findings}


@checker.check("prompt_version(): the same text gives the same id, any edit a new one, line endings do not matter")
def _():
    a = mod.prompt_version("You are the helpdesk.\nBe kind.")
    assert a == mod.prompt_version("You are the helpdesk.\r\nBe kind.\n") and a.startswith("p-") and len(a) == 14
    assert a != mod.prompt_version("You are the helpdesk.\nBe kind!")


@checker.check("compare(): unchanged and improved categories are ok")
def _():
    assert set(levels(mod.compare(BASE, BASE)).values()) == {"ok"}
    found = {f["category"]: f for f in mod.compare(BASE, with_(memory=4))}
    assert found["memory"]["level"] == "ok" and "improved" in found["memory"]["reason"]


@checker.check("compare(): safety fails on any drop; other categories fail beyond the tolerance or below the bar")
def _():
    assert levels(mod.compare(BASE, with_(safety=3), tolerance=5))["safety"] == "fail"
    assert levels(mod.compare(BASE, with_(grounding=5), tolerance=0))["grounding"] == "fail"
    assert levels(mod.compare(BASE, with_(grounding=5), tolerance=1))["grounding"] == "warn"
    assert levels(mod.compare(BASE, with_(arithmetic=2), tolerance=2))["arithmetic"] == "fail", \
        "2/4 is below the capstone's 75% bar, whatever the tolerance"


@checker.check("compare(): a dropped category fails, a new one warns")
def _():
    found = levels(mod.compare(BASE, with_(memory=None, tool_use=4)))
    assert found["memory"] == "fail" and found["tool_use"] == "warn", found


@checker.check("gate(): pass/fail, a report with both releases and every category, and a hint to approve")
def _():
    baseline = {"release": RELEASE, "results": BASE, "approved_by": "maya", "approved_at": "2026-11-15"}
    ok, report = mod.gate(baseline, RELEASE, BASE)
    assert ok and report.startswith("# Release gate: PASSED") and "maya" in report
    assert all(c in report for c in BASE), "every category in the table"
    new_release = {**RELEASE, "prompt_version": "p-ccc"}
    ok, report = mod.gate(baseline, new_release, with_(memory=4))
    assert ok and "p-ccc (changed)" in report and "approve" in report, report
    ok, report = mod.gate(baseline, new_release, with_(safety=3))
    assert not ok and report.startswith("# Release gate: FAILED")


@checker.check("replay: the recorded replies, scored by the capstone's own code, reproduce the baseline")
def _():
    recorded = json.loads(mod.RECORDINGS.read_text(encoding="utf-8"))
    rows = asyncio.run(mod.run(mod.Replayer(recorded["replies"])))
    baseline = json.loads(mod.BASELINE.read_text(encoding="utf-8"))
    assert mod.results_from_rows(rows) == baseline["results"], "recordings and baseline must agree"
    assert recorded["release"] == baseline["release"]
    assert mod.changed(recorded["release"], mod.current_release(recorded["release"]["model"])) == [], \
        "the recordings were made with the current prompt and tools"


@checker.check("replay refuses recordings made for another prompt")
def _():
    old = {**mod.current_release("m"), "prompt_version": "p-000000000000"}
    assert mod.changed(old, mod.current_release("m")) == ["prompt_version"]


@checker.check("the workflow: replay on pull requests without secrets, live by hand with secrets, reports uploaded")
def _():
    workflow = yaml.safe_load(checker.path("release-gate.yml").read_text(encoding="utf-8"))
    triggers = workflow.get("on", workflow.get(True))  # YAML reads a bare `on` as true
    assert "pull_request" in triggers and "workflow_dispatch" in triggers
    jobs = workflow["jobs"]
    replay = next(j for j in jobs.values() if "pull_request" in str(j.get("if", "")))
    live = next(j for j in jobs.values() if "workflow_dispatch" in str(j.get("if", "")))
    replay_text, live_text = yaml.safe_dump(replay), yaml.safe_dump(live)
    assert "gate --replay" in replay_text and "secrets." not in replay_text, "replay must not need secrets"
    assert "gate --live" in live_text and "secrets." in live_text
    for job in (replay, live):
        uploads = [s for s in job["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact")]
        assert uploads and uploads[0].get("if") == "always()", "upload the report, also when the gate fails"
        assert "release_gate.md" in yaml.safe_dump(uploads[0])


checker.run()
