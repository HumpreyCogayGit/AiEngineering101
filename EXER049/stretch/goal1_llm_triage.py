"""EXER049 stretch goal 1 — let a model pre-triage the review queue, and check it against the person.

    uv run python EXER049/stretch/goal1_llm_triage.py

Reviewing 29 traces by hand each week is fine; 2,900 is not. A model can do a
first pass: read the question, the answer and what the documents say, and
propose a verdict. It is a judge, so it gets the EXER024 treatment: compare it
with human labels before trusting it. reviews.json holds the person's verdicts
for this queue.

The useful number is not the overall agreement but the misses: a failure the
model calls "ok" never reaches a person.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from aicourse.llm import get_chat_model
from aicourse.rag import format_docs, get_vector_store
from aicourse.stretch import solution_module

base = solution_module(__file__, "feedback_loop.py")


class Triage(BaseModel):
    reason: str = Field(description="One sentence: what the documents say, and whether the answer matches")
    verdict: Literal["ok", "fail"]


PROMPT = """You review answers of the Nimbus Coffee helpdesk. The answer must agree with the documents.
An answer that says "I don't know" when the documents DO answer the question is a failure.

Documents:
{docs}

Customer question: {question}
Helpdesk answer: {answer}"""


def main() -> None:
    traces = base.load_traces()
    queue = base.sample_for_review(traces, base.implicit_signals(traces), random_k=10, seed=49)
    human = json.loads(base.REVIEWS.read_text(encoding="utf-8"))
    judge = get_chat_model(temperature=0).with_structured_output(Triage)
    store = get_vector_store()
    agree, missed, extra = 0, [], []
    for trace in queue:
        docs = format_docs(store.similarity_search(trace["question"], k=3))
        result = judge.invoke(PROMPT.format(docs=docs, question=trace["question"], answer=trace["answer"]))
        truth = human[trace["trace_id"]]["verdict"]
        agree += result.verdict == truth
        if truth == "fail" and result.verdict == "ok":
            missed.append(trace)
        if truth == "ok" and result.verdict == "fail":
            extra.append(trace)
        mark = "  " if result.verdict == truth else "<>"
        print(f"{mark} {trace['trace_id']} person={truth:<4} model={result.verdict:<4} {trace['question'][:42]:<42} {result.reason[:60]}")
    print(f"\nagreement {agree}/{len(queue)}; failures the model called ok: {len(missed)}; "
          f"ok answers it flagged: {len(extra)}")
    print("A missed failure is the expensive error: tune the prompt until it is 0 on these, then spot-check weekly.")


if __name__ == "__main__":
    main()
