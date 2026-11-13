"""EXER003 — HTTP and the Raw API Call (reference solution).

We call the chat model with nothing but an HTTP library (httpx). No SDK.
Everything an SDK does for you is visible here.
"""

from __future__ import annotations

import json

import httpx

from aicourse.settings import get_settings


def build_url(base_url: str) -> str:
    """The chat completions URL of an OpenAI-compatible v1 API."""
    return f"{base_url.rstrip('/')}/chat/completions"


def build_headers(api_key: str) -> dict[str, str]:
    """The key travels as a Bearer token in the `Authorization` header."""
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def build_body(model: str, prompt: str) -> dict:
    """`model` is the name your provider knows the model by."""
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }


def send_chat(prompt: str, model: str | None = None) -> dict:
    """POST the request and return the parsed JSON response.

    Raises httpx.HTTPStatusError for 4xx/5xx responses.
    `model` overrides the configured chat model (used to test a wrong name).
    """
    s = get_settings()
    response = httpx.post(
        build_url(s.base_url),
        headers=build_headers(s.api_key.get_secret_value()),
        json=build_body(model or s.chat_model, prompt),
        timeout=s.request_timeout,
    )
    response.raise_for_status()
    return response.json()


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
