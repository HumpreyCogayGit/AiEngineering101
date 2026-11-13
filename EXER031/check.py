"""EXER031 checks. Run:  uv run python EXER031/check.py"""

from langchain_core.messages import AIMessage

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("team.py")
searches = []


def fake_search(query):
    searches.append(query)
    return "[1] (source: company_faq.md)\nPets are welcome at the BGC café."


LAST_LLM = {}


def team_with(*routes, replies=("- Pets welcome at BGC [company_faq.md]", "Dear customer... Nimbus Support")):
    searches.clear()
    structured = [mod.Route(next=r, instruction=f"do {r}") for r in routes]
    LAST_LLM["llm"] = fake_chat_model(*replies, structured=structured)
    return mod.build_team(LAST_LLM["llm"], fake_search)


@checker.check("the team graph has a supervisor and two workers")
def _():
    nodes = set(team_with("FINISH").get_graph().nodes)
    assert {"supervisor", "researcher", "writer"} <= nodes, nodes


@checker.check("supervisor -> researcher -> supervisor -> writer -> supervisor -> FINISH")
def _():
    result = team_with("researcher", "writer", "FINISH").invoke({"messages": [("user", "Can I bring my dog?")]})
    assert result["steps"] == ["researcher", "writer"], result["steps"]
    names = [getattr(m, "name", None) for m in result["messages"]]
    assert names[-2:] == ["researcher", "writer"], names


@checker.check("only each worker's final answer is added to the shared conversation")
def _():
    result = team_with("researcher", "writer", "FINISH").invoke({"messages": [("user", "dog?")]})
    assert len(result["messages"]) == 3, [type(m).__name__ for m in result["messages"]]
    assert mod.final_reply(result).startswith("Dear customer")


@checker.check("the supervisor's instruction reaches the worker")
def _():
    team_with("researcher", "FINISH").invoke({"messages": [("user", "dog?")]})
    worker_calls = [msgs for msgs in LAST_LLM["llm"].received if isinstance(msgs, list)
                    and any("[Supervisor → researcher] do researcher" in str(getattr(m, "content", "")) for m in msgs)]
    assert worker_calls, "the researcher never received the supervisor's instruction"


@checker.check("MAX_STEPS stops a supervisor that never finishes")
def _():
    result = team_with("researcher").invoke({"messages": [("user", "loop")]})
    assert len(result["steps"]) == mod.MAX_STEPS, result["steps"]


@checker.check("the supervisor cannot FINISH before the writer has replied (a rule enforced in code)")
def _():
    result = team_with("researcher", "FINISH").invoke({"messages": [("user", "dog?")]})
    assert result["steps"] == ["researcher", "writer"], result["steps"]
    result = team_with("FINISH").invoke({"messages": [("user", "dog?")]})
    assert result["steps"] == ["researcher", "writer"], result["steps"]


def handoff_team(*replies):
    searches.clear()
    LAST_LLM["llm"] = fake_chat_model(*replies)
    return mod.build_handoff_team(LAST_LLM["llm"], fake_search)


SEARCH_CALL = AIMessage(content="", tool_calls=[{"name": "search_documents", "args": {"query": "dogs"}, "id": "call_1"}])


@checker.check("handoff: the researcher passes control straight to the writer with Command(goto=...)")
def _():
    team = handoff_team(SEARCH_CALL, "- Pets welcome at BGC [company_faq.md]", "Dear customer... Nimbus Support")
    assert "supervisor" not in set(team.get_graph().nodes), "the handoff team has no supervisor"
    result = team.invoke({"messages": [("user", "Can I bring my dog?")]})
    assert result["steps"] == ["researcher", "writer"], result["steps"]
    assert searches == ["dogs"], searches
    assert mod.final_reply(result).startswith("Dear customer")
    assert len(LAST_LLM["llm"].received) == 3, "3 model calls: no supervisor round trips"


@checker.check("handoff: with nothing to research, the researcher ends the run itself")
def _():
    result = handoff_team("Hello! How can I help?").invoke({"messages": [("user", "hi")]})
    assert result["steps"] == ["researcher"], result["steps"]
    assert len(result["messages"]) == 2


@checker.check("a real team answers using the documents  [live API]")
def _():
    team = mod.build_team(get_chat_model(temperature=0), mod.kb_search)
    result = team.invoke({"messages": [("user", "Customer asks: can I bring my dog to your café?")]})
    reply = mod.final_reply(result)
    assert "researcher" in result["steps"] and "writer" in result["steps"], result["steps"]
    assert "BGC" in reply, reply


@checker.check("a real handoff team gives the same answer with fewer model calls  [live API]")
def _():
    team = mod.build_handoff_team(get_chat_model(temperature=0), mod.kb_search)
    result = team.invoke({"messages": [("user", "Customer asks: can I bring my dog to your café?")]})
    assert result["steps"] == ["researcher", "writer"], result["steps"]
    assert "BGC" in mod.final_reply(result), mod.final_reply(result)


checker.run()
