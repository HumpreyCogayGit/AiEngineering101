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

# Remembers what your chat model supports, so the detection call runs only once.
_CAPABILITY_CACHE = ROOT_DIR / ".aicourse_cache.json"
# Set by the check runner so offline checks never make a detection call.
_force_supports_temperature: bool | None = None


def supports_temperature() -> bool:
    """Does your chat model accept a custom `temperature`?

    Classic chat models (gpt-4.1, gpt-4o, and the open models Ollama runs)
    accept 0 to 2. Hosted reasoning models (the gpt-5 family, o-series) only
    accept the default and answer `400 Unsupported value: 'temperature'` for
    anything else.

    Order of precedence: AICOURSE_SUPPORTS_TEMPERATURE in `.env`, then the
    cached answer, then one tiny detection call to the model.
    """
    if _force_supports_temperature is not None:
        return _force_supports_temperature
    s = get_settings()
    if s.supports_temperature is not None:
        return s.supports_temperature
    key = f"{s.endpoint}|{s.chat_model}|temperature"
    try:
        cache = json.loads(_CAPABILITY_CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}
    if key in cache:
        return bool(cache[key])
    try:
        get_llm_client().chat.completions.create(
            model=s.chat_model,
            messages=[{"role": "user", "content": "hi"}],
            temperature=0,
            **{s.max_tokens_param: 16},
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


def model_params(
    temperature: float | None = None, max_tokens: int | None = None, **extra: Any
) -> dict[str, Any]:
    """Keyword arguments for a model call that are safe for YOUR provider and model.

        client.chat.completions.create(model=..., messages=..., **model_params(temperature=0))

    `temperature` is included only when the model accepts it (see
    `supports_temperature`). `max_tokens` is sent under the name your provider
    understands (see `Settings.max_tokens_param`). `reasoning_effort` is added
    when one is configured (see `Settings.reasoning_effort`). Anything else is
    passed through unchanged, and wins over the configured values.
    """
    params: dict[str, Any] = {}
    if get_settings().reasoning_effort is not None:
        params["reasoning_effort"] = get_settings().reasoning_effort
    params.update(extra)
    if temperature is not None and supports_temperature():
        params["temperature"] = temperature
    if max_tokens is not None:
        params[get_settings().max_tokens_param] = max_tokens
    return params


def get_llm_client() -> OpenAI:
    """Synchronous client for your provider's OpenAI-compatible API.

    The `openai` SDK is the client library for that API, whoever serves it:
    the same object talks to Azure Foundry and to a local Ollama.
    """
    s = get_settings()
    return OpenAI(
        base_url=s.base_url,
        api_key=s.api_key.get_secret_value(),
        timeout=s.request_timeout,
    )


def get_async_llm_client() -> AsyncOpenAI:
    """Async version of `get_llm_client()`."""
    s = get_settings()
    return AsyncOpenAI(
        base_url=s.base_url,
        api_key=s.api_key.get_secret_value(),
        timeout=s.request_timeout,
    )


def get_chat_model(**kwargs: Any):
    """LangChain chat model for your configured chat model.

    Extra keyword arguments (temperature, max_tokens, streaming, ...) are
    passed straight to `ChatOpenAI`, LangChain's class for any
    OpenAI-compatible API. `temperature` is dropped when your model does not
    accept it (reasoning models such as the gpt-5 family).

    Read answers with `message.text`, not `message.content`: depending on the
    model, `content` is either a string or a list of content blocks.
    """
    from langchain_openai import ChatOpenAI

    s = get_settings()
    params: dict[str, Any] = {
        "model": s.chat_model,
        "base_url": s.base_url,
        "api_key": s.api_key.get_secret_value(),
        "timeout": s.request_timeout,
        "max_retries": 2,
    }
    if s.reasoning_effort is not None:
        params["reasoning_effort"] = s.reasoning_effort
    params.update(kwargs)
    if params.get("temperature") is not None and not supports_temperature():
        params.pop("temperature")
    return ChatOpenAI(**params)


def _make_prefixed_embeddings_class():
    from langchain_openai import OpenAIEmbeddings

    class PrefixedEmbeddings(OpenAIEmbeddings):
        """Embeddings that put a fixed text in front of every query / document.

        Some embedding models are trained with task prefixes and need them to
        retrieve well. The stored documents themselves stay unchanged: only the
        text sent to the embedding model gets the prefix.
        """

        query_prefix: str = ""
        document_prefix: str = ""

        def embed_documents(self, texts, *args, **kwargs):
            return super().embed_documents([self.document_prefix + t for t in texts], *args, **kwargs)

        async def aembed_documents(self, texts, *args, **kwargs):
            return await super().aembed_documents([self.document_prefix + t for t in texts], *args, **kwargs)

        def embed_query(self, text, **kwargs):
            # The parent would route this through embed_documents and add the wrong prefix.
            return OpenAIEmbeddings.embed_documents(self, [self.query_prefix + text], **kwargs)[0]

        async def aembed_query(self, text, **kwargs):
            return (await OpenAIEmbeddings.aembed_documents(self, [self.query_prefix + text], **kwargs))[0]

    return PrefixedEmbeddings


def get_embeddings(**kwargs: Any):
    """LangChain embeddings model for your configured embedding model.

    Applies the configured query / document prefixes, if any
    (see `Settings.embedding_query_prefix`).
    """
    from langchain_openai import OpenAIEmbeddings

    s = get_settings()
    params: dict[str, Any] = {
        "model": s.embedding_model,
        "base_url": s.base_url,
        "api_key": s.api_key.get_secret_value(),
        # Send plain text rather than pre-tokenized input; works with every provider.
        "check_embedding_ctx_length": False,
    }
    params.update(kwargs)
    if s.embedding_query_prefix or s.embedding_document_prefix:
        return _make_prefixed_embeddings_class()(
            query_prefix=s.embedding_query_prefix, document_prefix=s.embedding_document_prefix, **params
        )
    return OpenAIEmbeddings(**params)
