"""EXER010 checks (offline — the LLM is replaced by a fake). Run:  uv run python EXER010/check.py"""

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from aicourse.check import Checker
from aicourse.fakes import FakeClient

checker = Checker(__file__)
mod = checker.load("ask.py")
runner = CliRunner()


def use_fake(text="The answer is 42"):
    fake = FakeClient(stream_text=text)
    mod.get_client = lambda: fake
    return fake


def invoke(args, **kw):
    result = runner.invoke(mod.app, args, **kw)
    if isinstance(result.exception, NotImplementedError):
        raise result.exception
    return result


@checker.check("--help lists the ask, chat and summarize commands")
def _():
    out = invoke(["--help"]).output
    for cmd in ("ask", "chat", "summarize"):
        assert cmd in out, f"command '{cmd}' not found in --help"


@checker.check("ask streams the answer to stdout")
def _():
    fake = use_fake("The answer is 42")
    result = invoke(["ask", "meaning of life?"])
    assert result.exit_code == 0, result.output
    assert "The answer is 42" in result.output
    assert fake.calls[0]["stream"] is True


@checker.check("ask --system and -t are sent to the model")
def _():
    fake = use_fake()
    invoke(["ask", "hi", "--system", "Be a pirate", "-t", "0.2"])
    call = fake.calls[0]
    assert call["messages"][0] == {"role": "system", "content": "Be a pirate"}
    assert call["temperature"] == 0.2


@checker.check("summarize reads a file and puts --words in the prompt")
def _():
    fake = use_fake("Short summary")
    with tempfile.TemporaryDirectory() as tmp:
        doc = Path(tmp) / "doc.txt"
        doc.write_text("A very long document about llamas.")
        result = invoke(["summarize", str(doc), "--words", "30"])
    assert result.exit_code == 0, result.output
    sent = fake.calls[0]["messages"]
    assert "30" in sent[0]["content"] and "llamas" in sent[1]["content"]


@checker.check("summarize - reads from stdin (piping)")
def _():
    fake = use_fake()
    result = invoke(["summarize", "-"], input="Text from a pipe about owls.")
    assert result.exit_code == 0, result.output
    assert "owls" in fake.calls[0]["messages"][1]["content"]


@checker.check("summarize on a missing file exits with code 1 and an error")
def _():
    use_fake()
    result = invoke(["summarize", "does-not-exist.txt"])
    assert result.exit_code == 1, f"exit code {result.exit_code}"
    assert "not found" in result.output.lower()


checker.run()
