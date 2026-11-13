"""EXER003 checks. The last two make real API calls. Run:  uv run python EXER003/check.py"""

import httpx

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("raw_call.py")


@checker.check("build_url() appends /openai/v1/chat/completions")
def _():
    assert mod.build_url("https://x.openai.azure.com") == "https://x.openai.azure.com/openai/v1/chat/completions"


@checker.check("build_url() handles a trailing slash")
def _():
    assert mod.build_url("https://x.openai.azure.com/") == "https://x.openai.azure.com/openai/v1/chat/completions"


@checker.check("build_headers() sends the key in `api-key` and JSON content type")
def _():
    h = mod.build_headers("secret")
    assert h.get("api-key") == "secret"
    assert h.get("Content-Type") == "application/json"


@checker.check("build_body() uses the deployment as model with one user message")
def _():
    assert mod.build_body("dep", "Hi") == {"model": "dep", "messages": [{"role": "user", "content": "Hi"}]}


@checker.check("send_chat() returns a chat.completion with text  [live API]")
def _():
    data = mod.send_chat("Reply with the single word: pong")
    assert "choices" in data, f"unexpected response: {data}"
    assert data["choices"][0]["message"]["content"], "empty reply"
    assert data["usage"]["total_tokens"] > 0


@checker.check("send_chat() raises HTTPStatusError 401 for a wrong key  [live API]")
def _():
    try:
        mod.send_chat("hi", api_key="wrong-key")
    except httpx.HTTPStatusError as exc:
        assert exc.response.status_code == 401, exc.response.status_code
        return
    raise AssertionError("no error raised — did you call response.raise_for_status()?")


checker.run()
