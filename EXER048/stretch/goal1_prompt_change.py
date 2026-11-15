"""EXER048 stretch goal 1 — take one prompt change through the gate, the way a pull request would.

    uv run python EXER048/stretch/goal1_prompt_change.py

The recorded baseline has memory at 3/4: asked "What's my name?" after saying
it, the capstone answered "I don't know, your name isn't in the Nimbus
documents". Its system prompt says to answer ONLY from the documents, and the
model applied that to the conversation too.

The fix is one sentence in the prompt. This script plays the pull request:
1. patch the prompt (in memory: the reference solution is not changed),
2. show that REPLAY refuses: the prompt version no longer matches the recordings,
3. run the LIVE evaluation with the new prompt and gate it against the baseline,
4. print the report. Approving it is a person's decision, so the script stops there.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from aicourse.stretch import solution_module

gate = solution_module(__file__, "release_gate.py")
capstone = gate.capstone

FIX = ("\n- What the user told you earlier in THIS conversation (their name, where they live, what they want "
       "to order) is not outside knowledge: use it.")


async def main() -> None:
    model = gate.model_name()
    recorded = gate.json.loads(gate.RECORDINGS.read_text(encoding="utf-8"))
    capstone.SYSTEM_PROMPT += FIX
    release = gate.current_release(model)
    print(f"prompt version {recorded['release']['prompt_version']} -> {release['prompt_version']}")
    print(f"replay: {', '.join(gate.changed(recorded['release'], release))} changed since recording -> REFUSED, "
          "a live run is needed\n")
    with tempfile.TemporaryDirectory() as tmp:
        rows = await gate.run(await gate.live_assistant(Path(tmp)))
    passed, report = gate.gate(gate.json.loads(gate.BASELINE.read_text(encoding="utf-8")), release,
                               gate.results_from_rows(rows))
    print(report)
    print("A reviewer reads this report on the pull request, and approves the new baseline only if it is better.")


if __name__ == "__main__":
    asyncio.run(main())
