"""Answer-level errors. They are preserved in results, never converted to `unknown`."""
from __future__ import annotations

import re

_SECRET_RE = re.compile(r"(sk-[A-Za-z0-9_\-]{8,})|((?:api[_-]?key|authorization|bearer)[\"'=:\s]+[A-Za-z0-9_\-\.]{8,})", re.I)


def sanitize(message: object, limit: int = 300) -> str:
    text = _SECRET_RE.sub("[redacted]", str(message))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


class AgentError(Exception):
    error_type = "agent_error"
    http_status = 502

    def __init__(self, message: str):
        super().__init__(message)
        self.message = sanitize(message)

    def as_dict(self) -> dict:
        return {"type": self.error_type, "message": self.message}


class ProviderFailure(AgentError):
    error_type = "provider_error"


class ProviderTimeout(AgentError):
    error_type = "provider_timeout"
    http_status = 504


class InvalidOutput(AgentError):
    error_type = "invalid_output"


class ToolError(AgentError):
    error_type = "tool_error"


class TurnLimitExceeded(AgentError):
    error_type = "turn_limit_exceeded"


class UnknownBrand(ValueError):
    """Raised by the catalogue for an unknown brand id."""
