"""EXER037 stretch goal 2 — the EXER035 tracker on the evaluation run, and its cost.

    uv run python EXER037/stretch/goal2_eval_cost.py

`Reply.tokens` gives one number per answer. The EXER035 tracker gives the
whole picture: every model call and tool call of the run, input and output
tokens apart, and a cost. It is attached once, to the agent, with
`with_config(callbacks=[...])`; the assistant's code does not change.

The prices are the example values from EXER035. Put your provider's prices in
PRICES to get your real cost; a local model costs nothing per token.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from aicourse.stretch import solution_module, solution_path

solution_path(__file__)
import assistant as assistant_module  # noqa: E402
import evaluate  # noqa: E402
import tools as tools_module  # noqa: E402

observability = solution_module(__file__, "observability.py", exercise="EXER035")
PRICES = observability.PRICES


async def main() -> None:
    cases = json.loads(evaluate.EVAL_SET.read_text(encoding="utf-8"))
    tracker = observability.UsageTracker()
    with tempfile.TemporaryDirectory() as tmp:
        tools = tools_module.LOCAL_TOOLS + await tools_module.load_mcp_tools(Path(tmp) / "notes.json")
        helpdesk = await assistant_module.Assistant(tools=tools).setup()
        helpdesk.agent = helpdesk.agent.with_config(callbacks=[tracker])  # every nested call reports to the tracker
        rows = await evaluate.run_eval(helpdesk, cases)

    report = tracker.report(PRICES)
    answered = [r for r in rows if r["tokens"]]  # blocked questions never reach the model
    print(f"{sum(r['passed'] for r in rows)}/{len(rows)} cases passed\n")
    for key in ("llm_calls", "tool_calls", "errors", "input_tokens", "output_tokens"):
        print(f"{key:<15}{report[key]:>10}")
    print(f"{'cost_usd':<15}{report['cost_usd']:>10.5f}   (at ${PRICES['input']}/1M input, ${PRICES['output']}/1M output)")
    print(f"\nPer answered question: {report['llm_calls'] / len(answered):.1f} model calls, "
          f"${report['cost_usd'] / len(answered):.5f}")
    costly = max(answered, key=lambda r: r["tokens"])
    print(f"Most expensive question ({costly['tokens']} tokens): {costly['question']}")
    share = report["input_tokens"] / (report["input_tokens"] + report["output_tokens"])
    print(f"Input tokens are {share:.0%} of all tokens: the documents returned by search are what you pay for.")


if __name__ == "__main__":
    asyncio.run(main())
