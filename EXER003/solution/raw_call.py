"""EXER003 — HTTP and the Raw API Call (reference solution).

We call the chat model with nothing but an HTTP library (httpx). No SDK.
Everything an SDK does for you is visible here.
"""

from __future__ import annotations

import json

import httpx

from aicourse.settings import get_settings


def build_url(endpoint: str) -> str:
    """The chat completions URL of Azure's OpenAI-compatible v1 API."""
    return f"{endpoint.rstrip('/')}/openai/v1/chat/completions"


def build_headers(api_key: str) -> dict[str, str]:
    """Azure accepts the key in the `api-key` header."""
    return {"api-key": api_key, "Content-Type": "application/json"}


def build_body(deployment: str, prompt: str) -> dict:
    """On Azure, `model` is your DEPLOYMENT name."""
    return {
        "model": deployment,
        "messages": [{"role": "user", "content": prompt}],
    }


def send_chat(prompt: str, api_key: str | None = None) -> dict:
    """POST the request and return the parsed JSON response.

    Raises httpx.HTTPStatusError for 4xx/5xx responses.
    `api_key` overrides the configured key (used to test a wrong key).
    """
    s = get_settings()
    key = api_key if api_key is not None else s.api_key.get_secret_value()
    response = httpx.post(
        build_url(s.endpoint),
        headers=build_headers(key),
        json=build_body(s.chat_deployment, prompt),
        timeout=s.request_timeout,
    )
    response.raise_for_status()
    return response.json()


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
