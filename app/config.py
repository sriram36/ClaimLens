"""Runtime configuration — reads from environment, never from code.

All secrets (API key, DB URL) come from env vars only. Nothing here is
committed to the repo with actual credentials.
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env_file(path: Path | None = None) -> None:
    """Read a local .env file into os.environ if present, without overwriting existing env."""
    p = path or (ROOT / ".env")
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'\""))


@dataclass(frozen=True)
class Settings:
    # Azure deployment name doubles as the "model" identifier in reports
    deployment: str = "gpt-5.6-luna"
    api_version: str = "2024-10-21"
    provider_timeout_s: float = 120.0
    max_tokens: int = 4096
    max_retries: int = 2
    # Temperature None omits the parameter (required by newer Azure reasoning models)
    temperature: float | None = None
    data_dir: Path = ROOT / "data"
    prompt_dir: Path = ROOT / "prompts"

    @classmethod
    def from_env(cls) -> "Settings":
        load_env_file()
        d = cls()
        def _get_val(key_suffix: str, default: str) -> str:
            # Check CLAIMLENS_ prefix first, then legacy KASPARRO_ prefix
            return os.getenv(f"CLAIMLENS_{key_suffix}") or os.getenv(f"KASPARRO_{key_suffix}") or default

        temp_str = _get_val("TEMPERATURE", "")
        temp: float | None = (
            None if temp_str.strip().lower() == "none"
            else float(temp_str) if temp_str.strip()
            else d.temperature
        )
        return cls(
            deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", d.deployment),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", d.api_version),
            provider_timeout_s=float(_get_val("TIMEOUT_S", str(d.provider_timeout_s))),
            max_tokens=int(_get_val("MAX_TOKENS", str(d.max_tokens))),
            max_retries=int(_get_val("MAX_RETRIES", str(d.max_retries))),
            temperature=temp,
            data_dir=Path(_get_val("DATA_DIR", str(d.data_dir))),
        )

    def public(self) -> dict:
        """Return settings that are safe to store in run metadata (no secrets)."""
        out = asdict(self)
        out.pop("data_dir")
        out.pop("prompt_dir")
        out["max_turns"] = 3
        return out
