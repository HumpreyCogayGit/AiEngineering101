"""EXER003 — HTTP and the Raw API Call.

Call the chat model with nothing but an HTTP library (httpx). No SDK.
Complete every TODO, then run:

    uv run python EXER003/starter/raw_call.py
    uv run python EXER003/check.py
"""

from __future__ import annotations

import json

import httpx

from aicourse.settings import get_settings


def build_url(base_url: str) -> str:
    """The chat completions URL of an OpenAI-compatible v1 API.

    "http://localhost:11434/v1/" -> "http://localhost:11434/v1/chat/completions"
    Be careful not to produce a double slash if the base URL ends with "/".
    """
    # TODO
    raise NotImplementedError("build_url")


def build_headers(api_key: str) -> dict[str, str]:
    """Return the HTTP headers.

    The key travels as a Bearer token: `Authorization: Bearer <api_key>`.
    We also send `Content-Type: application/json`.
    """
    # TODO
    raise NotImplementedError("build_headers")


def build_body(model: str, prompt: str) -> dict:
    """Return the JSON body: {"model": model, "messages": [one user message]}.

    `model` is the name your provider knows the model by. (You wrote this in EXER002!)
    """
    # TODO
    raise NotImplementedError("build_body")


def send_chat(prompt: str, model: str | None = None) -> dict:
    """POST the request and return the parsed JSON response.

    `model` overrides the configured chat model (used to test a wrong name).

    Steps:
      1. s = get_settings()
      2. url = build_url(s.base_url); key = s.api_key.get_secret_value()
      3. httpx.post(url, headers=..., json=build_body(model or s.chat_model, prompt),
                    timeout=s.request_timeout)
      4. response.raise_for_status()   # turns 4xx/5xx into an exception
      5. return response.json()
    """
    # TODO
    raise NotImplementedError("send_chat")


def main() -> None:
    prompt = "In one sentence, what is a large language model?"
    print(f">>> POST {build_url(get_settings().base_url)}")
    data = send_chat(prompt)
    print("\n--- Full JSON response ---")
    print(json.dumps(data, indent=2)[:1500])
    print("\n--- What you actually care about ---")
    print("Reply        :", data["choices"][0]["message"]["content"])
    print("Finish reason:", data["choices"][0]["finish_reason"])
    print("Usage        :", data["usage"])

    print("\n--- And with a model that does not exist ---")
    try:
        send_chat(prompt, model="no-such-model")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP {exc.response.status_code}: {exc.response.text[:200]}")


if __name__ == "__main__":
    main()
