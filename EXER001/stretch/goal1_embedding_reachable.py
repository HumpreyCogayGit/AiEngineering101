"""EXER001 stretch goal 1 — report whether the embedding model is reachable.

    uv run python EXER001/stretch/goal1_embedding_reachable.py

check_setup.py proves that your settings LOAD. It does not prove that the
embedding model answers, and you only find that out in EXER019. This version
asks the provider for one tiny embedding and reports the result.

It needs one HTTP request, which is the subject of EXER003. Come back to this
goal after EXER003 if the request below looks unfamiliar.
"""

from __future__ import annotations

import httpx

from aicourse.settings import Settings
from aicourse.stretch import solution_module

base = solution_module(__file__, "check_setup.py")


def embedding_reachable(settings: Settings) -> tuple[bool, str]:
    """Return (reachable, detail). Never raises: a setup check must always finish."""
    try:
        response = httpx.post(
            f"{settings.base_url}embeddings",
            headers={"Authorization": f"Bearer {settings.api_key.get_secret_value()}"},
            json={"model": settings.embedding_model, "input": ["ping"]},
            timeout=settings.request_timeout,
        )
    except httpx.HTTPError as exc:  # no network, wrong host, server not running
        return False, f"no answer from {settings.endpoint} ({type(exc).__name__})"
    if response.status_code != 200:
        return False, f"HTTP {response.status_code}: {response.text[:120]}"
    dimensions = len(response.json()["data"][0]["embedding"])
    return True, f"{dimensions} dimensions"


def main() -> None:
    settings = base.load_config()
    print(f"Provider        : {settings.provider_label}")
    print(f"Embedding model : {settings.embedding_model}")
    ok, detail = embedding_reachable(settings)
    print(f"Reachable       : {'yes' if ok else 'NO'} ({detail})")


if __name__ == "__main__":
    main()
