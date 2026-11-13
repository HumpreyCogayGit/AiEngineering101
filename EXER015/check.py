"""EXER015 checks. Run:  uv run python EXER015/check.py

The app itself is tested headless with Streamlit's AppTest, using a fake model.
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from streamlit.testing.v1 import AppTest

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model

checker = Checker(__file__)
logic = checker.load("chat_logic.py")
APP = str(checker.path("app.py"))


@checker.check("to_langchain_messages() converts roles to message classes")
def _():
    msgs = logic.to_langchain_messages(
        [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}], "S")
    assert [type(m) for m in msgs] == [SystemMessage, HumanMessage, AIMessage]
    assert msgs[0].content == "S" and msgs[2].content == "hello"


@checker.check("stream_answer() yields text pieces")
def _():
    pieces = list(logic.stream_answer(fake_chat_model("streamed reply here"), [{"role": "user", "content": "x"}], "S"))
    assert "".join(pieces) == "streamed reply here" and len(pieces) > 1, pieces


def run_app():
    """Run app.py headless with load_llm() patched to return a fake model."""
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception, at.exception
    return at


@checker.check("the app renders a title, chat input and sidebar settings")
def _():
    at = run_app()
    assert at.title[0].value.endswith("Course Chat")
    assert len(at.chat_input) == 1
    assert len(at.sidebar.text_area) == 1 and len(at.sidebar.slider) == 1


@checker.check("the sidebar has a Clear conversation button")
def _():
    at = run_app()
    labels = [b.label for b in at.sidebar.button]
    assert any("clear" in label.lower() for label in labels), labels


@checker.check("sending a message shows the user and assistant bubbles and stores history")
def _():
    import aicourse.llm as llm_module
    original = llm_module.get_chat_model
    llm_module.get_chat_model = lambda **kw: fake_chat_model("Hello from the fake model")
    try:
        at = run_app()
        at.chat_input[0].set_value("Hi there").run()
        assert not at.exception, at.exception
        history = at.session_state["messages"]
        assert [m["role"] for m in history] == ["user", "assistant"], history
        assert history[1]["content"] == "Hello from the fake model"
        assert [m.name for m in at.chat_message] == ["user", "assistant"]
    finally:
        llm_module.get_chat_model = original


checker.run()
