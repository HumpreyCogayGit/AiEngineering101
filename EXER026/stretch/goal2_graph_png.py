"""EXER026 stretch goal 2 — draw the graph to a PNG.

    uv run python EXER026/stretch/goal2_graph_png.py

`draw_mermaid()` gives the diagram as text. To get a picture:

1. This script always writes the Mermaid text to output/ticket_graph.mmd
   (offline, no dependencies).
2. With --png it also asks LangGraph for a PNG. By default LangGraph renders
   through the public mermaid.ink web service, so that step needs a network
   connection and SENDS YOUR DIAGRAM TEXT to that service. Do not use it for
   a graph whose node names are confidential; render the .mmd file locally
   instead (for example with the Mermaid CLI, or by pasting it into a page
   that loads Lecture/assets/vendor/mermaid.min.js).

The README shows the result: ![graph](ticket_graph.png)
"""

from __future__ import annotations

import sys
from pathlib import Path

from aicourse.stretch import solution_module

base = solution_module(__file__, "ticket_graph.py")

OUTPUT = Path(__file__).resolve().parent / "output"


def write_mermaid(graph, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(graph.get_graph().draw_mermaid(), encoding="utf-8")
    return path


def write_png(graph, path: Path) -> Path | None:
    """Render through LangGraph's default renderer (the mermaid.ink service). None if it fails."""
    try:
        data = graph.get_graph().draw_mermaid_png()
    except Exception as exc:  # no network, service down, proxy...
        print(f"Could not render a PNG ({type(exc).__name__}: {str(exc)[:80]}). The .mmd file still works.")
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def main() -> None:
    graph = base.build_graph()
    mmd = write_mermaid(graph, OUTPUT / "ticket_graph.mmd")
    print(f"Mermaid text written to {mmd.relative_to(mmd.parents[3])}")
    nodes = graph.get_graph().nodes
    print(f"The graph has {len(nodes)} nodes: {', '.join(nodes)}")
    if "--png" in sys.argv:
        png = write_png(graph, OUTPUT / "ticket_graph.png")
        if png:
            print(f"PNG written to {png.relative_to(png.parents[3])} ({png.stat().st_size:,} bytes)")
    else:
        print("Add --png to render a picture through mermaid.ink (sends the diagram text to that service).")


if __name__ == "__main__":
    main()
