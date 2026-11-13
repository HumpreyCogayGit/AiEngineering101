"""Fake LLM clients used by the check scripts.

They let a check verify WHAT your code sends to the model (offline, free and
deterministic) without making a real API call. You never need these in your
own exercise code.
"""

from __future__ import annotations

import json
from types import SimpleNamespace as NS
from typing import Any


def _message(content: str | None = None, tool_calls: list[dict] | None = None):
    tcs = None
    if tool_calls:
        tcs = [
            NS(
                id=tc["id"],
                type="function",
                function=NS(name=tc["name"], arguments=json.dumps(tc["arguments"])),
            )
            for tc in tool_calls
        ]
    msg = NS(role="assistant", content=content, tool_calls=tcs)

    def model_dump(**_: Any) -> dict:
        d: dict[str, Any] = {"role": "assistant", "content": content}
        if tcs:
            d["tool_calls"] = [
                {"id": t.id, "type": "function",
                 "function": {"name": t.function.name, "arguments": t.function.arguments}}
                for t in tcs
            ]
        return d

    msg.model_dump = model_dump
    return msg


def make_response(content: str | None = None, tool_calls: list[dict] | None = None,
                  finish_reason: str | None = None):
    """Build an object shaped like openai's ChatCompletion."""
    return NS(
        id="chatcmpl-fake",
        model="fake",
        choices=[NS(index=0, message=_message(content, tool_calls),
                    finish_reason=finish_reason or ("tool_calls" if tool_calls else "stop"))],
        usage=NS(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )


def make_chunk(content: str | None = None, finish_reason: str | None = None, usage: bool = False):
    if usage:
        return NS(choices=[], usage=NS(prompt_tokens=10, completion_tokens=5, total_tokens=15))
    return NS(choices=[NS(index=0, delta=NS(content=content, role=None, tool_calls=None),
                          finish_reason=finish_reason)], usage=None)


def fake_chat_model(*replies: Any, structured: list[Any] | None = None):
    """A scripted LangChain chat model (offline). See FakeChatModel."""
    import itertools

    from langchain_core.messages import AIMessage

    msgs = [r if isinstance(r, AIMessage) else AIMessage(content=r) for r in (replies or ("fake reply",))]
    # Fresh copies (id=None) so LangGraph's message reducer appends instead of de-duplicating.
    stream = (m.model_copy(update={"id": None}) for m in itertools.chain(msgs, itertools.repeat(msgs[-1])))
    return __getattr__("FakeChatModel")(messages=stream, structured=list(structured or []))


def _make_fake_chat_model_class():
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
    from langchain_core.runnables import RunnableLambda
    from pydantic import Field

    class FakeChatModel(GenericFakeChatModel):
        """Returns scripted AIMessages in order (the last one repeats forever).

        - records every list of input messages in `.received`
        - `bind_tools()` works (records the tools in `.bound_tools`) and returns the same model
        - `with_structured_output()` returns the objects in `structured` one by one
        """

        received: list = Field(default_factory=list)
        bound_tools: list = Field(default_factory=list)
        structured: list = Field(default_factory=list)

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            self.received.append(list(messages))
            return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

        def _stream(self, messages, stop=None, run_manager=None, **kwargs):
            self.received.append(list(messages))
            yield from super()._stream(messages, stop=stop, run_manager=run_manager, **kwargs)

        def bind_tools(self, tools, **kwargs):
            self.bound_tools = list(tools)
            return self

        def with_structured_output(self, schema, **kwargs):
            def pick(_input):
                self.received.append(_input)
                return self.structured.pop(0) if len(self.structured) > 1 else self.structured[0]
            return RunnableLambda(pick)

    return FakeChatModel


def __getattr__(name: str):
    # Lazy so that importing aicourse.fakes doesn't import LangChain in Module 1.
    if name == "FakeChatModel":
        if "FakeChatModel" in globals():
            return globals()["FakeChatModel"]
        cls = _make_fake_chat_model_class()
        globals()["FakeChatModel"] = cls
        return cls
    raise AttributeError(name)


class FakeClient:
    """Records every create() call and returns scripted replies in order.

    replies: list of str (plain text), dict (make_response kwargs) or Exception.
    """

    def __init__(self, replies: list[Any] | None = None, stream_text: str = "Hello there friend"):
        self.replies = list(replies or ["fake reply"])
        self.stream_text = stream_text
        self.calls: list[dict] = []
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kwargs: Any):
        self.calls.append(json.loads(json.dumps(kwargs, default=str)))
        if kwargs.get("stream"):
            return self._stream(kwargs)
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, dict):
            return make_response(**reply)
        return make_response(content=reply)

    def _stream(self, kwargs: dict):
        words = self.stream_text.split(" ")
        yield make_chunk(content="")
        for i, w in enumerate(words):
            yield make_chunk(content=w if i == 0 else " " + w)
        yield make_chunk(finish_reason="stop")
        if (kwargs.get("stream_options") or {}).get("include_usage"):
            yield make_chunk(usage=True)
