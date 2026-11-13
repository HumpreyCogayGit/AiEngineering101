"""EXER013 checks. Run:  uv run python EXER013/check.py"""

from langchain_core.prompts import ChatPromptTemplate

from aicourse.check import Checker
from aicourse.fakes import fake_chat_model
from aicourse.llm import get_chat_model

checker = Checker(__file__)
mod = checker.load("chains.py")


@checker.check("summary_prompt is a ChatPromptTemplate with {text} and {max_words}")
def _():
    if mod.summary_prompt is None:
        raise NotImplementedError("summary_prompt")
    assert isinstance(mod.summary_prompt, ChatPromptTemplate)
    assert set(mod.summary_prompt.input_variables) == {"text", "max_words"}, mod.summary_prompt.input_variables


@checker.check("translate_prompt uses {summary} and {language}")
def _():
    if mod.translate_prompt is None:
        raise NotImplementedError("translate_prompt")
    assert set(mod.translate_prompt.input_variables) == {"summary", "language"}


@checker.check("build_summary_chain() returns a plain string")
def _():
    llm = fake_chat_model("A short summary.")
    out = mod.build_summary_chain(llm).invoke({"text": "long text", "max_words": 10})
    assert out == "A short summary.", repr(out)
    rendered = llm.received[0][-1].content
    assert "long text" in rendered and "10" in rendered, "the template variables were not filled in"


@checker.check("build_pipeline() keeps the inputs and adds summary + translation")
def _():
    llm = fake_chat_model("SUMMARY", "TRANSLATION")
    out = mod.build_pipeline(llm).invoke({"text": "t", "max_words": 5, "language": "French"})
    assert out["summary"] == "SUMMARY" and out["translation"] == "TRANSLATION", out
    assert out["language"] == "French" and out["text"] == "t"
    assert "SUMMARY" in llm.received[1][-1].content, "the translation step must receive the summary"


@checker.check("the pipeline translates a real summary  [live API]")
def _():
    out = mod.build_pipeline(get_chat_model(temperature=0)).invoke(
        {"text": mod.ARTICLE, "max_words": 30, "language": "Spanish"})
    assert len(out["summary"].split()) <= 45, f"summary has {len(out['summary'].split())} words"
    assert out["translation"] and out["translation"] != out["summary"]


checker.run()
