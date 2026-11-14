"""EXER003 stretch goal 2 — print the rate-limit headers of the response.

    uv run python EXER003/stretch/goal2_rate_limit_headers.py

A response is more than its body. A hosted provider reports how much of your
quota is left in headers such as `x-ratelimit-remaining-requests`. EXER011
uses the same idea (the `Retry-After` header) to decide how long to wait.
A local Ollama has no quota, so it sends none.
"""

from __future__ import annotations

import httpx

from aicourse.settings import get_settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "raw_call.py")


def rate_limit_headers(response: httpx.Response) -> dict[str, str]:
    """The headers about quota and retrying. Header names are case-insensitive."""
    return {
        name: value
        for name, value in response.headers.items()
        if "ratelimit" in name.lower() or name.lower() == "retry-after"
    }


def main() -> None:
    s = get_settings()
    response = httpx.post(
        base.build_url(s.base_url),
        headers=base.build_headers(s.api_key.get_secret_value()),
        json=base.build_body(s.chat_model, "Say hi."),
        timeout=s.request_timeout,
    )
    response.raise_for_status()
    print(f"HTTP {response.status_code} from {s.provider_label}")
    found = rate_limit_headers(response)
    for name, value in found.items():
        print(f"  {name}: {value}")
    if not found:
        print("  (no rate-limit headers: this provider does not meter requests)")


if __name__ == "__main__":
    main()
