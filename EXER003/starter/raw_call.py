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


def build_url(endpoint: str) -> str:
    """The chat completions URL of Azure's OpenAI-compatible v1 API.

    "https://x.openai.azure.com" -> "https://x.openai.azure.com/openai/v1/chat/completions"
    Be careful not to produce a double slash if the endpoint ends with "/".
    """
    # TODO
    raise NotImplementedError("build_url")


def build_headers(api_key: str) -> dict[str, str]:
    """Return the HTTP headers.

    Azure accepts the key in a header called `api-key`.
    We also send `Content-Type: application/json`.
    """
    # TODO
    raise NotImplementedError("build_headers")


def build_body(deployment: str, prompt: str) -> dict:
    """Return the JSON body: {"model": deployment, "messages": [one user message]}.

    On Azure, `model` is your DEPLOYMENT name. (You wrote this in EXER002!)
    """
    # TODO
    raise NotImplementedError("build_body")


def send_chat(prompt: str, api_key: str | None = None) -> dict:
    """POST the request and return the parsed JSON response.

    Steps:
      1. s = get_settings()
      2. key = api_key if api_key is not None else s.api_key.get_secret_value()
      3. httpx.post(url, headers=..., json=..., timeout=s.request_timeout)
      4. response.raise_for_status()   # turns 4xx/5xx into an exception
      5. return response.json()
    """
    # TODO
    raise NotImplementedError("send_chat")


def main() -> None:
    prompt = "In one sentence, what is a large language model?"
    print(f">>> POST {build_url(get_settings().endpoint)}")
    data = send_chat(prompt)
    print("\n--- Full JSON response ---")
    print(json.dumps(data, indent=2)[:1500])
    print("\n--- What you actually care about ---")
    print("Reply        :", data["choices"][0]["message"]["content"])
    print("Finish reason:", data["choices"][0]["finish_reason"])
    print("Usage        :", data["usage"])

    print("\n--- And with a wrong key ---")
    try:
        send_chat(prompt, api_key="wrong-key")
    except httpx.HTTPStatusError as exc:
        print(f"HTTP {exc.response.status_code}: {exc.response.text[:200]}")


if __name__ == "__main__":
    main()
