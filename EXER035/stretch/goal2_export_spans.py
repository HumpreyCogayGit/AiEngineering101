"""EXER035 stretch goal 2 (part 1) — export the spans as JSON.

    uv run python EXER035/stretch/goal2_export_spans.py                    # runs the agent, writes trace.json
    uv run streamlit run EXER035/stretch/goal2_timeline_app.py             # part 2: draw it

A trace you can only print is a trace you read once. As JSON it can be
stored, compared between versions, and drawn. Each span becomes one object;
times are seconds from the start of the trace, so the file needs no clock.
"""

from __future__ import annotations

import json
from pathlib import Path

from aicourse.stretch import solution_module

base = solution_module(__file__, "observability.py")

TRACE_FILE = Path(__file__).resolve().parent / "output" / "trace.json"


def spans_as_dicts(tracker) -> list[dict]:
    spans = sorted(tracker.spans.values(), key=lambda s: s.start)
    if not spans:
        return []
    origin = spans[0].start
    return [{
        "kind": s.kind,
        "name": s.name,
        "start": round(s.start - origin, 3),
        "end": round((s.end or s.start) - origin, 3),
        "seconds": round(s.duration, 3),
        "input_tokens": s.input_tokens,
        "output_tokens": s.output_tokens,
        "detail": s.detail,
        "error": s.error,
        "id": str(s.run_id),
        "parent": str(s.parent_run_id) if s.parent_run_id else None,
    } for s in spans]


def export(tracker, question: str, path: Path = TRACE_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"question": question, "report": tracker.report(), "spans": spans_as_dicts(tracker)}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def main() -> None:
    tracker = base.UsageTracker()
    question = "What is the refund window for unopened beans, and is shipping free?"
    result = base.build_agent().invoke({"messages": [("user", question)]}, {"callbacks": [tracker]})
    print("A:", result["messages"][-1].text[:160])
    path = export(tracker, question)
    print(f"\n{len(tracker.spans)} spans written to {path.relative_to(path.parents[3])}")
    print("Now run:  uv run streamlit run EXER035/stretch/goal2_timeline_app.py")


if __name__ == "__main__":
    main()
