"""EXER031 stretch goal 1 — a reviewer that can send the draft back once.

    uv run python EXER031/stretch/goal1_reviewer.py

A third specialist joins the handoff team. The reviewer checks the writer's
draft against the research and either approves it or hands it back with
feedback:

    researcher -> writer -> reviewer --approved--------------> END
                    ^           |
                    +--revise---+      (at most MAX_REVISIONS times)

"Once" is counted in the state and enforced in code. Without the limit, a
strict reviewer and a stubborn writer would pass the draft back and forth
forever: the ping-pong from the lecture.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel, Field

from aicourse.llm import get_chat_model
from aicourse.stretch import solution_module

base = solution_module(__file__, "team.py")

MAX_REVISIONS = 1


class Review(BaseModel):
    feedback: str = Field(description="What must change, in one or two sentences. Empty if nothing.")
    approved: bool = Field(description="True if the draft answers every question in the customer's email "
                                       "using only researched facts")


class ReviewState(base.TeamState):
    revisions: int


REVIEWER_PROMPT = (
    "You review a draft customer reply for Nimbus Coffee Co. Check three things: (1) it answers EVERY "
    "question in the customer's email, (2) every fact appears in the researcher's notes, (3) it is under "
    "120 words and signed 'Nimbus Support'. Approve only if all three hold."
)


def build_review_team(llm, search, reviewer=None):
    researcher, writer = base.make_workers(llm, search)
    reviewer = reviewer or llm.with_structured_output(Review)

    def research(state: ReviewState) -> Command:
        result = researcher.invoke({"messages": state["messages"]})
        note = AIMessage(content=result["messages"][-1].text, name="researcher")
        return Command(goto="writer", update={"messages": [note], "steps": ["researcher"]})

    def write(state: ReviewState) -> Command:
        result = writer.invoke({"messages": state["messages"]})
        draft = AIMessage(content=result["messages"][-1].text, name="writer")
        return Command(goto="reviewer", update={"messages": [draft], "steps": ["writer"]})

    def review(state: ReviewState) -> Command:
        verdict = reviewer.invoke([SystemMessage(REVIEWER_PROMPT)] + state["messages"])
        done = state.get("revisions", 0) >= MAX_REVISIONS
        if verdict.approved or done:  # approved, or out of revisions: the draft stands
            note = "approved" if verdict.approved else f"not approved, but the revision limit is reached: {verdict.feedback}"
            return Command(goto=END, update={"messages": [AIMessage(content=note, name="reviewer")],
                                             "steps": ["reviewer"]})
        request = HumanMessage(content=f"[Reviewer → writer] Revise the draft: {verdict.feedback}")
        return Command(goto="writer", update={"messages": [request], "steps": ["reviewer"],
                                              "revisions": state.get("revisions", 0) + 1})

    builder = StateGraph(ReviewState)
    builder.add_node("researcher", research, destinations=("writer",))
    builder.add_node("writer", write, destinations=("reviewer",))
    builder.add_node("reviewer", review, destinations=("writer", END))
    builder.add_edge(START, "researcher")
    return builder.compile()


class StrictReviewer:
    """A scripted reviewer that never approves: proves the loop still ends."""

    def invoke(self, messages) -> Review:
        return Review(feedback="Make it warmer.", approved=False)


def main() -> None:
    llm = get_chat_model(temperature=0)
    request = ("Customer email: 'Hi! My grinder arrived broken yesterday, and I also wonder if I can "
               "bring my dog when I pick up a replacement at your café?'")
    for label, reviewer in (("the model as reviewer", None), ("a reviewer that never approves", StrictReviewer())):
        result = build_review_team(llm, base.kb_search, reviewer).invoke({"messages": [("user", request)]})
        verdict = [m for m in result["messages"] if getattr(m, "name", None) == "reviewer"][-1].text
        print(f"\n=== {label} ===")
        print("steps   :", " -> ".join(result["steps"]))
        print("verdict :", verdict[:120])
        print("reply   :", base.final_reply(result)[:230].replace("\n", " "))


if __name__ == "__main__":
    main()
