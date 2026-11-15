"""EXER047 stretch goal 2 — traces that never contain personal data (EXER035).

    uv run python EXER047/stretch/goal2_redacting_tracker.py

The EXER035 tracker stores the first 60 characters of every tool input, and
error messages as they are. When a customer asks the helpdesk to save a note
with their phone number, that number goes into the trace, and traces are kept
longer and shown to more people than conversations.

RedactingTracker is the same tracker with every text it stores passed through
this lesson's redact(). Both trackers watch the same live question; the script
prints what each one stored.
"""

from __future__ import annotations

import asyncio
import tempfile
import uuid
from pathlib import Path

from aicourse.stretch import solution_module, solution_path

base = solution_module(__file__, "privacy.py")
observability = solution_module(__file__, "observability.py", exercise="EXER035")
solution_path(__file__, exercise="EXER037")
import assistant as capstone  # noqa: E402
import tools as capstone_tools  # noqa: E402


class RedactingTracker(observability.UsageTracker):
    """Redacts tool inputs and error texts before they are stored."""

    def on_tool_start(self, serialized, input_str, **kwargs):
        super().on_tool_start(serialized, base.redact(input_str), **kwargs)

    def on_tool_error(self, error, *, run_id, **kwargs):
        super().on_tool_error(error, run_id=run_id, **kwargs)
        if run_id in self.spans and self.spans[run_id].error:
            self.spans[run_id].error = base.redact(self.spans[run_id].error)

    def on_llm_error(self, error, *, run_id, **kwargs):
        super().on_llm_error(error, run_id=run_id, **kwargs)
        if run_id in self.spans and self.spans[run_id].error:
            self.spans[run_id].error = base.redact(self.spans[run_id].error)


async def main() -> None:
    plain, redacting = observability.UsageTracker(), RedactingTracker()
    with tempfile.TemporaryDirectory() as tmp:
        tools = capstone_tools.LOCAL_TOOLS + await capstone_tools.load_mcp_tools(Path(tmp) / "notes.json")
        helpdesk = await capstone.Assistant(tools=tools).setup()
        helpdesk.agent = helpdesk.agent.with_config(callbacks=[plain, redacting])
        await helpdesk.ask("Save a note titled 'Callback': call 0917 555 0142 or ana@example.com",
                           uuid.uuid4().hex)
    for label, tracker in (("EXER035 tracker", plain), ("redacting      ", redacting)):
        for span in tracker.spans.values():
            if span.kind == "tool":
                print(f"{label}  {span.name}: {span.detail}")
    leaked = any("0917" in s.detail or "ana@" in s.detail for s in redacting.spans.values())
    print("\nThe redacting tracker stored no phone number or email." if not leaked else "\nLEAK: check redact()")


if __name__ == "__main__":
    asyncio.run(main())
