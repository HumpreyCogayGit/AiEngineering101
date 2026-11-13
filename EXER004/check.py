"""EXER004 checks. Run:  uv run python EXER004/check.py"""

from openai import OpenAI

from aicourse.check import Checker

checker = Checker(__file__)
mod = checker.load("sdk_basics.py")


@checker.check("make_client() returns an SDK client on your provider's v1 base URL")
def _():
    from aicourse.settings import get_settings

    client = mod.make_client()
    assert isinstance(client, OpenAI)
    assert str(client.base_url) == get_settings().base_url, client.base_url


@checker.check("count_tokens('hello world') == 2")
def _():
    assert mod.count_tokens("hello world") == 2, mod.count_tokens("hello world")


@checker.check("estimate_cost() uses per-million pricing")
def _():
    cost = mod.estimate_cost(1_000_000, 500_000, 0.40, 1.60)
    assert abs(cost - 1.20) < 1e-9, cost
    assert abs(mod.estimate_cost(100, 0, 2.0, 8.0) - 0.0002) < 1e-12


@checker.check("ask() returns text, token usage and finish reason  [live API]")
def _():
    r = mod.ask(mod.make_client(), "Say hello in French. One word.")
    assert r.text.strip(), "empty text"
    assert r.prompt_tokens > 0 and r.completion_tokens > 0
    assert r.finish_reason == "stop", r.finish_reason


@checker.check("ask(max_tokens=5) stops early with finish_reason='length'  [live API]")
def _():
    r = mod.ask(mod.make_client(), "Write a 500 word essay about the sea.", max_tokens=5)
    assert r.finish_reason == "length", r.finish_reason
    assert r.completion_tokens <= 5


@checker.check("temperature_experiment() returns runs answers per temperature  [live API]")
def _():
    out = mod.temperature_experiment(mod.make_client(), "Pick a random fruit. One word.", [0.0, 1.0], runs=2)
    assert set(out) == {0.0, 1.0}
    assert len(out[1.0]) == 2, "temperature 1.0 is the default: every model accepts it"
    # Reasoning models (gpt-5 family) reject 0.0: an empty list is the right answer there.
    assert len(out[0.0]) in (0, 2), out[0.0]


@checker.check("temperature_experiment() survives a model that rejects the temperature")
def _():
    import httpx
    from openai import BadRequestError

    from aicourse.fakes import FakeClient

    request = httpx.Request("POST", "https://offline-check.invalid")
    rejected = BadRequestError(
        "Unsupported value: 'temperature' does not support 0 with this model.",
        response=httpx.Response(400, request=request), body=None,
    )
    out = mod.temperature_experiment(FakeClient([rejected, "Mango", "Kiwi"]), "Pick a fruit.", [0.0, 1.0], runs=2)
    assert out == {0.0: [], 1.0: ["Mango", "Kiwi"]}, out


checker.run()
