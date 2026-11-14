"""EXER035 stretch goal 2 (part 2) — draw the exported trace in Streamlit (EXER015).

    uv run python EXER035/stretch/goal2_export_spans.py        # first: creates output/trace.json
    uv run streamlit run EXER035/stretch/goal2_timeline_app.py

One horizontal bar per span, from its start to its end, model calls and tool
calls in different colours. Gaps and long bars are visible at a glance, which
is the reason tracing tools draw timelines instead of printing lists.
"""

import json
from pathlib import Path

import streamlit as st

TRACE_FILE = Path(__file__).resolve().parent / "output" / "trace.json"

st.set_page_config(page_title="Trace timeline", page_icon="⏱", layout="wide")
st.title("⏱ Trace timeline")

if not TRACE_FILE.exists():
    st.info("No trace yet. Run `uv run python EXER035/stretch/goal2_export_spans.py` first.")
    st.stop()

trace = json.loads(TRACE_FILE.read_text(encoding="utf-8"))
report, spans = trace["report"], trace["spans"]
st.caption(f"Question: {trace['question']}")

columns = st.columns(4)
columns[0].metric("Model calls", report["llm_calls"])
columns[1].metric("Tool calls", report["tool_calls"])
columns[2].metric("Tokens", report["input_tokens"] + report["output_tokens"])
columns[3].metric("Cost (USD)", f"{report['cost_usd']:.5f}")

rows = [{**s, "step": f"{i + 1:02d} {s['kind'].upper()} {s['name']}", "status": "error" if s["error"] else s["kind"]}
        for i, s in enumerate(spans)]
st.vega_lite_chart(
    rows,
    {
        "mark": {"type": "bar", "cornerRadius": 3},
        "encoding": {
            "y": {"field": "step", "type": "nominal", "sort": None, "title": None},
            "x": {"field": "start", "type": "quantitative", "title": "seconds since the start of the run"},
            "x2": {"field": "end"},
            "color": {"field": "status", "type": "nominal", "title": None,
                      "scale": {"domain": ["llm", "tool", "error"], "range": ["#0b6e6e", "#b35c00", "#b42318"]}},
            "tooltip": [{"field": "name"}, {"field": "seconds"}, {"field": "input_tokens"},
                        {"field": "output_tokens"}, {"field": "detail"}, {"field": "error"}],
        },
        "height": max(120, 34 * len(rows)),
    },
    width="stretch",
)

st.subheader("Spans")
st.dataframe([{k: s[k] for k in ("kind", "name", "start", "seconds", "input_tokens", "output_tokens", "detail", "error")}
              for s in spans], hide_index=True)
biggest = max((s for s in spans if s["kind"] == "llm"), key=lambda s: s["input_tokens"], default=None)
if biggest:
    st.caption(f"Largest input: {biggest['input_tokens']} tokens, in the model call that starts at {biggest['start']}s.")
