"""Provider abstraction.

AzureProvider talks to Azure OpenAI using the openai SDK.
FakeProvider is a scripted stand-in used only in tests.

The ProviderResponse type is our internal format — the rest of the codebase
never sees raw SDK objects, which makes swapping providers straightforward.
"""
from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass, field
from typing import Callable, Protocol

from .errors import ProviderFailure, ProviderTimeout


@dataclass
class ProviderResponse:
    # List of dicts, each either:
    #   {"type": "text", "text": "..."}
    #   {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
    content: list
    stop_reason: str | None = None
    usage: dict = field(default_factory=dict)


class Provider(Protocol):
    name: str
    model: str

    def create(
        self,
        *,
        system: str,
        messages: list,
        tools: list,
        tool_choice: dict,
        max_tokens: int,
        timeout: float,
    ) -> ProviderResponse: ...


# ---------------------------------------------------------------------------
# Azure OpenAI provider
# ---------------------------------------------------------------------------

# Map our internal tool_choice vocab (borrowed from Anthropic) to OpenAI's.
_CHOICE_MAP = {"any": "required", "auto": "auto", "none": "none"}


def _build_tools(tools: list) -> list:
    """Convert our tool schema (Anthropic-style) to OpenAI function format."""
    out = []
    for t in tools:
        out.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t["input_schema"],
            },
        })
    return out


def _to_openai_messages(system: str, messages: list) -> list:
    """
    Translate our internal message list (which uses Anthropic-style content
    blocks) into OpenAI chat messages.

    Our internal format looks like:
        [{"role": "user", "content": "..."}]          # plain text
        [{"role": "assistant", "content": [blocks]}]  # after a tool call
        [{"role": "user", "content": [tool_results]}] # tool results

    We prepend the system prompt as the first message.
    """
    out = [{"role": "system", "content": system}]
    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue

        # content is a list of blocks
        if role == "assistant":
            # Could be text blocks and/or tool_use blocks
            text_parts = [b["text"] for b in content if b.get("type") == "text"]
            tool_calls = [
                {
                    "id": b["id"],
                    "type": "function",
                    "function": {
                        "name": b["name"],
                        # OpenAI expects arguments as a JSON string
                        "arguments": json.dumps(b["input"]),
                    },
                }
                for b in content
                if b.get("type") == "tool_use"
            ]
            msg_out: dict = {"role": "assistant"}
            if text_parts:
                msg_out["content"] = " ".join(text_parts)
            else:
                msg_out["content"] = None
            if tool_calls:
                msg_out["tool_calls"] = tool_calls
            out.append(msg_out)

        elif role == "user":
            # Could be tool results (list of tool_result blocks)
            if isinstance(content, list) and content and content[0].get("type") == "tool_result":
                for tr in content:
                    out.append({
                        "role": "tool",
                        "tool_call_id": tr["tool_use_id"],
                        "content": tr["content"],
                    })
            else:
                # Shouldn't really happen but handle gracefully
                out.append({"role": "user", "content": str(content)})

    return out


def _parse_response(resp) -> ProviderResponse:
    """Turn an OpenAI ChatCompletion into our internal ProviderResponse."""
    choice = resp.choices[0]
    msg = choice.message
    finish = choice.finish_reason

    blocks = []

    # Text content
    if msg.content:
        blocks.append({"type": "text", "text": msg.content})

    # Tool calls
    if msg.tool_calls:
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}
            blocks.append({
                "type": "tool_use",
                "id": tc.id,
                "name": tc.function.name,
                "input": args,
            })

    # Map OpenAI finish_reason back to Anthropic-style stop_reason so the
    # agent loop doesn't need to care which provider is underneath.
    stop = "tool_use" if finish == "tool_calls" else "end_turn"

    usage = {}
    if resp.usage:
        usage = {
            "input_tokens": resp.usage.prompt_tokens,
            "output_tokens": resp.usage.completion_tokens,
        }

    return ProviderResponse(blocks, stop, usage)


class AzureProvider:
    """Azure OpenAI via the openai SDK (AzureOpenAI client)."""

    name = "azure"

    def __init__(
        self,
        deployment: str,
        api_key: str | None = None,
        endpoint: str | None = None,
        api_version: str | None = None,
        max_retries: int = 2,
        temperature: float | None = 0.0,
    ):
        from openai import AzureOpenAI, APITimeoutError, APIError

        import re
        key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        ep = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        ver = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")

        if not key:
            raise ProviderFailure("AZURE_OPENAI_API_KEY is not set")
        if not ep:
            raise ProviderFailure("AZURE_OPENAI_ENDPOINT is not set")

        # Strip any trailing /openai/v1/responses or /openai/... paths if pasted
        ep = re.sub(r"/openai(/.*)?$", "", ep.strip())

        self._openai_errors = (APITimeoutError, APIError)
        self._timeout_error = APITimeoutError
        self.client = AzureOpenAI(
            api_key=key,
            azure_endpoint=ep,
            api_version=ver,
            max_retries=max_retries,
        )
        self.model = deployment   # In Azure land, "model" == deployment name
        self.temperature = temperature

    def create(self, *, system, messages, tools, tool_choice, max_tokens, timeout) -> ProviderResponse:
        oai_messages = _to_openai_messages(system, messages)
        oai_tools = _build_tools(tools)
        oai_choice = _CHOICE_MAP.get(tool_choice.get("type", "auto"), "auto")

        kwargs: dict = dict(
            model=self.model,
            messages=oai_messages,
            tools=oai_tools,
            tool_choice=oai_choice,
            timeout=timeout,
        )
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature

        try:
            try:
                # Newer Azure / OpenAI models require max_completion_tokens
                resp = self.client.chat.completions.create(max_completion_tokens=max_tokens, **kwargs)
            except self._openai_errors as e:
                if "max_completion_tokens" in str(e).lower() and "unsupported" in str(e).lower():
                    resp = self.client.chat.completions.create(max_tokens=max_tokens, **kwargs)
                else:
                    raise
        except self._timeout_error as e:
            raise ProviderTimeout(f"provider request timed out after {timeout}s") from e
        except self._openai_errors as e:  # type: ignore[misc]
            raise ProviderFailure(f"{type(e).__name__}: {e}") from e

        return _parse_response(resp)


# ---------------------------------------------------------------------------
# Fake provider (tests only)
# ---------------------------------------------------------------------------

class FakeProvider:
    """
    Scripted provider for controlled tests.

    `script` can be a list of ProviderResponse / Exception objects, or a
    callable that takes the kwargs dict and returns one of those.

    Every call's arguments are deep-copied into `.calls` so tests can inspect
    exactly what the agent sent.
    """

    name = "fake"

    def __init__(self, script: list | Callable, model: str = "fake-model"):
        self.script = script
        self.model = model
        self.calls: list[dict] = []

    def create(self, **kwargs) -> ProviderResponse:
        self.calls.append(copy.deepcopy(kwargs))
        item = self.script(kwargs) if callable(self.script) else self.script[len(self.calls) - 1]
        if callable(item):
            item = item(kwargs)
        if isinstance(item, Exception):
            raise item
        return item


# ---------------------------------------------------------------------------
# Helpers used by conftest / tests
# ---------------------------------------------------------------------------

def tool_use(name: str, tool_input: dict, tid: str = "tu_1") -> dict:
    return {"type": "tool_use", "id": tid, "name": name, "input": tool_input}


def text(t: str) -> dict:
    return {"type": "text", "text": t}
