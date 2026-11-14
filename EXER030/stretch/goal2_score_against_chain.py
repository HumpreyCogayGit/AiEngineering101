"""EXER030 stretch goal 2 — score the graph on the EXER024 set, against the plain chain.

    uv run python EXER030/stretch/goal2_score_against_chain.py        # first 6 questions
    uv run python EXER030/stretch/goal2_score_against_chain.py 20     # the whole golden set

Agentic RAG costs several extra model calls per question (one to route, one
per chunk to grade). Is the answer better for it? The EXER024 evaluation can
score anything that maps a question to {"docs", "answer"}, so a thin adapter
is enough to put the graph where the chain was. Model calls are counted with
a callback (EXER035), so the table shows quality AND price.
"""

from __future__ import annotations

import json
import sys

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableLambda

from aicourse.llm import get_chat_model
from aicourse.rag import build_rag_chain, get_vector_store
from aicourse.settings import DATA_DIR
from aicourse.stretch import solution_module

base = solution_module(__file__, "agentic_rag.py")
evaluation = solution_module(__file__, "evaluate.py", exercise="EXER024")


class CallCounter(BaseCallbackHandler):
    def __init__(self) -> None:
        self.calls = 0

    def on_chat_model_start(self, *args, **kwargs) -> None:
        self.calls += 1


def graph_as_chain(graph) -> RunnableLambda:
    """question -> {"question", "docs", "answer"}: the shape the evaluation expects."""
    def run(question: str, config) -> dict:
        state = graph.invoke({"question": question}, config)  # pass config on, so callbacks reach the graph
        # Score retrieval on what was retrieved; the answer was written from the relevant subset.
        return {"question": question, "docs": state.get("docs", []), "answer": state["answer"]}
    return RunnableLambda(run)


def evaluate(name: str, chain, judge_llm, dataset: list[dict]) -> dict:
    counter = CallCounter()
    counted = chain.with_config(callbacks=[counter])  # counts the system's calls, not the judge's
    rows = []
    for i, row in enumerate(dataset, 1):
        print(f"  [{name} {i}/{len(dataset)}] {row['question'][:60]}")
        rows.append(evaluation.evaluate_row(counted, judge_llm, row))
    return {**evaluation.summarize(rows), "model_calls_per_question": counter.calls / len(dataset)}


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    dataset = json.loads((DATA_DIR / "eval_questions.json").read_text(encoding="utf-8"))
    dataset = dataset[: limit - 1] + dataset[-1:]  # always keep the unanswerable question
    llm = get_chat_model(temperature=0)
    retriever = get_vector_store().as_retriever(search_kwargs={"k": 4})

    plain = evaluate("chain", build_rag_chain(retriever=retriever, llm=llm), llm, dataset)
    agentic = evaluate("graph", graph_as_chain(base.build_graph(llm, retriever)), llm, dataset)

    print(f"\n{'metric':<26}{'chain':>8}{'graph':>8}")
    for metric in ("hit_rate", "mrr", "faithfulness", "correctness", "refusal_rate", "model_calls_per_question"):
        print(f"{metric:<26}{plain[metric]:>8.2f}{agentic[metric]:>8.2f}")
    print("\nIf quality is equal, the extra calls bought nothing on these questions: fix retrieval first.")


if __name__ == "__main__":
    main()
