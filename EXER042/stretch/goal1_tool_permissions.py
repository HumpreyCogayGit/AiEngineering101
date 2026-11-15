"""EXER042 stretch goal 1 — authorize tools by role, on the server.

    uv run python EXER042/stretch/goal1_tool_permissions.py

The lesson filtered what each user may RETRIEVE. Tools need the same rule:
customers may search and calculate, only staff may write notes. The check
happens where the tools are handed to the agent. A tool that is never given
to the model cannot be called, however the question is phrased, which a
sentence in the system prompt cannot promise.

Both users below ask the same thing. The customer's assistant has no notes
tool to call; the staff assistant saves the note.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from aicourse.stretch import solution_module

base = solution_module(__file__, "secure_service.py")

TOOL_PERMISSIONS = {
    "customer": {"search_knowledge_base", "calculator"},
    "staff": {"search_knowledge_base", "calculator", "notes_add_note", "notes_list_notes", "notes_search_notes"},
}


def allowed_tools(principal, tools: list) -> list:
    """Only the tools this role may use. An unknown role gets nothing (deny by default)."""
    permitted = TOOL_PERMISSIONS.get(principal.role, set())
    return [t for t in tools if t.name in permitted]


class RoleAwareHelpdesks(base.UserHelpdesks):
    """The lesson's per-user assistants, with each tool list cut down to the user's role."""

    async def _assistant(self, principal):
        assistant = await super()._assistant(principal)
        if not getattr(assistant, "_role_checked", False):
            from langchain.agents import create_agent
            from langgraph.checkpoint.memory import InMemorySaver

            import assistant as capstone  # the EXER037 module, already on sys.path

            assistant.tools = allowed_tools(principal, assistant.tools)
            assistant.agent = create_agent(assistant.llm, assistant.tools, system_prompt=capstone.SYSTEM_PROMPT,
                                           checkpointer=InMemorySaver())
            assistant._role_checked = True
        return assistant


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base.NOTES_ROOT = Path(tmp)  # keep the demo's notes out of the real output folder
        tokens = base.TokenStore()
        users = {"ana (customer)": tokens.issue("ana", "customer"), "ben (staff)": tokens.issue("ben", "staff")}
        helpdesk = RoleAwareHelpdesks()
        question = "Please save a note titled 'Supplier' saying: call the Benguet co-op on Friday."
        for name, token in users.items():
            status, body, _ = base.route("POST", "/ask", {"Authorization": f"Bearer {token}"},
                                         json.dumps({"question": question}).encode(), helpdesk, tokens)
            print(f"{name}: HTTP {status}, tools used: {body.get('tools_used')}")
            print(f"   {body.get('answer', '')[:160]}")
        saved = sorted(p.name for p in Path(tmp).glob("*.json"))
        print(f"\nNotes files written: {saved or 'none'}")
        assert "ana.json" not in saved, "a customer must not be able to write notes"


if __name__ == "__main__":
    main()
