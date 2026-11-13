"""EXER024 — Evaluating RAG (reference solution).

"It looked fine when I tried three questions" is not evaluation. We measure:
  retrieval  — hit rate and MRR  (did we fetch the right document?)
  generation — faithfulness       (is the answer supported by the context?)
               correctness        (does it match the reference answer?)
               refusal            (does it say "I don't know" when it should?)
An LLM-as-judge scores what simple string matching can't.
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from aicourse.llm import get_chat_model
from aicourse.rag import NOT_FOUND, build_rag_chain, format_docs
from aicourse.settings import DATA_DIR

REPORT = Path(__file__).resolve().parent / "output" / "eval_report.md"


# ------------------------------------------------------------------ retrieval metrics
def reciprocal_rank(sources: list[str], expected: str) -> float:
    """1/position of the first correct source (1-based); 0 if not found."""
    for position, source in enumerate(sources, start=1):
        if source == expected:
            return 1.0 / position
    return 0.0


# ------------------------------------------------------------------ LLM-as-judge
class Grade(BaseModel):
    reasoning: str = Field(description="Short explanation, written BEFORE choosing the score")
    score: int = Field(ge=1, le=5, description="1 = very poor, 5 = excellent")


FAITHFULNESS_PROMPT = """You are grading a customer-support answer.
Score 1-5 how well EVERY claim in the answer is supported by the context.
5 = fully supported, 3 = partly supported, 1 = contradicts or invents facts.
An answer saying it doesn't know is fully faithful (5).

Context:
{context}

Question: {question}
Answer: {answer}"""

CORRECTNESS_PROMPT = """You are grading a customer-support answer against a reference answer.
Score 1-5 how well the answer matches the reference in meaning (wording may differ).
5 = same facts, 3 = partly right or missing key details, 1 = wrong.

Question: {question}
Reference answer: {reference}
Answer to grade: {answer}"""


def judge(judge_llm: BaseChatModel, prompt: str) -> Grade:
    return judge_llm.with_structured_output(Grade).invoke(prompt)


def judge_faithfulness(judge_llm: BaseChatModel, question: str, context: str, answer: str) -> Grade:
    return judge(judge_llm, FAITHFULNESS_PROMPT.format(context=context, question=question, answer=answer))


def judge_correctness(judge_llm: BaseChatModel, question: str, reference: str, answer: str) -> Grade:
    return judge(judge_llm, CORRECTNESS_PROMPT.format(question=question, reference=reference, answer=answer))


def is_refusal(answer: str) -> bool:
    return "don't know" in answer.lower() or NOT_FOUND.lower() in answer.lower()


# ------------------------------------------------------------------ the run
def evaluate_row(chain: Runnable, judge_llm: BaseChatModel, row: dict) -> dict:
    result = chain.invoke(row["question"])
    sources = [d.metadata.get("source") for d in result["docs"]]
    answer = result["answer"]
    out = {"question": row["question"], "answer": answer, "sources": sources}
    if row["expected_source"] is None:  # unanswerable: the right behaviour is to refuse
        out.update(hit=None, rr=None, faithfulness=5 if is_refusal(answer) else 1,
                   correctness=5 if is_refusal(answer) else 1, refused_correctly=is_refusal(answer))
        return out
    out["hit"] = row["expected_source"] in sources
    out["rr"] = reciprocal_rank(sources, row["expected_source"])
    out["faithfulness"] = judge_faithfulness(judge_llm, row["question"], format_docs(result["docs"]), answer).score
    out["correctness"] = judge_correctness(judge_llm, row["question"], row["reference_answer"], answer).score
    return out


def summarize(rows: list[dict]) -> dict:
    answerable = [r for r in rows if r["hit"] is not None]
    unanswerable = [r for r in rows if r["hit"] is None]
    return {
        "questions": len(rows),
        "hit_rate": sum(r["hit"] for r in answerable) / len(answerable),
        "mrr": statistics.mean(r["rr"] for r in answerable),
        "faithfulness": statistics.mean(r["faithfulness"] for r in rows),
        "correctness": statistics.mean(r["correctness"] for r in rows),
        "refusal_rate": (sum(r["refused_correctly"] for r in unanswerable) / len(unanswerable)) if unanswerable else None,
    }


def write_report(rows: list[dict], summary: dict, path: Path = REPORT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# RAG Evaluation Report", "", "| Metric | Value |", "|---|---|"]
    for key, value in summary.items():
        lines.append(f"| {key} | {value:.2f} |" if isinstance(value, float) else f"| {key} | {value} |")
    lines += ["", "| Question | Hit | Faithful | Correct | Answer |", "|---|---|---|---|---|"]
    for r in rows:
        hit = "–" if r["hit"] is None else ("✅" if r["hit"] else "❌")
        answer = r["answer"].replace("\n", " ").replace("|", "/")[:120]
        lines.append(f"| {r['question']} | {hit} | {r['faithfulness']} | {r['correctness']} | {answer} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    dataset = json.loads((DATA_DIR / "eval_questions.json").read_text(encoding="utf-8"))
    chain = build_rag_chain()
    judge_llm = get_chat_model(temperature=0)
    rows = []
    for i, row in enumerate(dataset, 1):
        print(f"[{i}/{len(dataset)}] {row['question']}")
        rows.append(evaluate_row(chain, judge_llm, row))
    summary = summarize(rows)
    print("\n" + json.dumps(summary, indent=2))
    print("Report written to", write_report(rows, summary))


if __name__ == "__main__":
    main()
