"""Ready-made clients for the course.

You build each of these by hand first (EXER003, EXER004, EXER012, EXER019).
After that, exercises use these helpers so they can focus on the new concept.

    from aicourse.llm import get_chat_model
    llm = get_chat_model()
    print(llm.invoke("Hello!").text)
"""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI, BadRequestError, OpenAI

from aicourse.settings import ROOT_DIR, get_settings

# Remembers what your deployment supports, so the detection call runs only once.
_CAPABILITY_CACHE = ROOT_DIR / ".aicourse_cache.json"
# Set by the check runner so offline checks never make a detection call.
_force_supports_temperature: bool | None = None


def supports_temperature() -> bool:
    """Does your chat deployment accept a custom `temperature`?

    Classic chat models (gpt-4.1, gpt-4o) accept 0 to 2. Reasoning models
    (the gpt-5 family, o-series) only accept the default and answer
    `400 Unsupported value: 'temperature'` for anything else.

    Order of precedence: AICOURSE_SUPPORTS_TEMPERATURE in `.env`, then the
    cached answer, then one tiny detection call to the deployment.
    """
    if _force_supports_temperature is not None:
        return _force_supports_temperature
    s = get_settings()
    if s.supports_temperature is not None:
        return s.supports_temperature
    key = f"{s.endpoint}|{s.chat_deployment}|temperature"
    try:
        cache = json.loads(_CAPABILITY_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    if key in cache:
        return bool(cache[key])
    try:
        get_openai_client().chat.completions.create(
            model=s.chat_deployment,
            messages=[{"role": "user", "content": "hi"}],
            temperature=0,
            max_completion_tokens=16,
        )
        supported = True
    except BadRequestError as exc:
        if "temperature" not in str(exc):
            return True  # some other problem: don't guess, don't cache
        supported = False
    except Exception:  # noqa: BLE001 - network or auth problem: let the real call report it
        return True
    cache[key] = supported
    try:
        _CAPABILITY_CACHE.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    except OSError:
        pass
    return supported


def model_params(temperature: float | None = None, **extra: Any) -> dict[str, Any]:
    """Keyword arguments for a model call that are safe for YOUR deployment.

        client.chat.completions.create(model=..., messages=..., **model_params(temperature=0))

    `temperature` is included only when the deployment accepts it (see
    `supports_temperature`). Anything else is passed through unchanged.
    """
    params = dict(extra)
    if temperature is not None and supports_temperature():
        params["temperature"] = temperature
    return params


def get_openai_client() -> OpenAI:
    """Synchronous OpenAI SDK client pointed at your Azure Foundry resource."""
    s = get_settings()
    return OpenAI(
        base_url=s.base_url,
        api_key=s.api_key.get_secret_value(),
        timeout=s.request_timeout,
    )


def get_async_openai_client() -> AsyncOpenAI:
    """Async version of `get_openai_client()`."""
    s = get_settings()
    return AsyncOpenAI(
        base_url=s.base_url,
        api_key=s.api_key.get_secret_value(),
        timeout=s.request_timeout,
    )


def get_chat_model(**kwargs: Any):
    """LangChain chat model for your chat deployment.

    Extra keyword arguments (temperature, max_tokens, streaming, ...) are
    passed straight to `ChatOpenAI`. `temperature` is dropped when your
    deployment does not accept it (reasoning models such as the gpt-5 family).

    Read answers with `message.text`, not `message.content`: depending on the
    model, `content` is either a string or a list of content blocks.
    """
    from langchain_openai import ChatOpenAI

    s = get_settings()
    params: dict[str, Any] = {
        "model": s.chat_deployment,
        "base_url": s.base_url,
        "api_key": s.api_key.get_secret_value(),
        "timeout": s.request_timeout,
        "max_retries": 2,
    }
    params.update(kwargs)
    if params.get("temperature") is not None and not supports_temperature():
        params.pop("temperature")
    return ChatOpenAI(**params)


def get_embeddings(**kwargs: Any):
    """LangChain embeddings model for your embedding deployment."""
    from langchain_openai import OpenAIEmbeddings

    s = get_settings()
    params: dict[str, Any] = {
        "model": s.embedding_deployment,
        "base_url": s.base_url,
        "api_key": s.api_key.get_secret_value(),
        # Send plain text rather than pre-tokenized input; works with every deployment.
        "check_embedding_ctx_length": False,
    }
    params.update(kwargs)
    return OpenAIEmbeddings(**params)
