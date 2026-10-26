"""Environment-backed configuration with safe defaults."""

from __future__ import annotations

import math
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


def _load_local_env() -> None:
    """Load simple KEY=VALUE entries from the project-local .env if present."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        if name:
            os.environ.setdefault(name, value)


_load_local_env()


def _env_or_override(name: str, overrides: Mapping[str, str] | None, default: str = "") -> str:
    if overrides and overrides.get(name):
        return str(overrides[name])
    return os.getenv(name, default)


class SettingsError(ValueError):
    """Raised when an environment-backed setting is invalid."""


def _as_bool(value: str, name: str = "setting") -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"{name} must be one of true/false, yes/no, or 1/0")


def _as_float(value: str, name: str, minimum: float, maximum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise SettingsError(f"{name} must be a number") from exc
    if not math.isfinite(parsed) or not minimum <= parsed <= maximum:
        raise SettingsError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _as_int(value: str, name: str, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise SettingsError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise SettingsError(f"{name} must be between {minimum} and {maximum}")
    return parsed


def _validate_url(value: str, name: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SettingsError(f"{name} must be an absolute http or https URL")
    if parsed.username or parsed.password:
        raise SettingsError(f"{name} must not contain embedded credentials")
    return value.rstrip("/")


@dataclass(frozen=True)
class Settings:
    api_key: str = ""
    model: str = "openrouter/free"
    base_url: str = "https://openrouter.ai/api/v1"
    site_url: str = "http://localhost:8501"
    app_name: str = "Northbridge Guide"
    min_retrieval_score: float = 0.16
    max_context_records: int = 4
    max_query_chars: int = 800
    max_requests_per_session: int = 30
    enable_dense_embeddings: bool = False

    @property
    def api_configured(self) -> bool:
        return bool(self.api_key.strip())


def get_settings(overrides: Mapping[str, str] | None = None) -> Settings:
    model = _env_or_override("OPENROUTER_MODEL", overrides, "openrouter/free").strip()
    app_name = _env_or_override("OPENROUTER_APP_NAME", overrides, "Northbridge Guide").strip()
    if not model:
        raise SettingsError("OPENROUTER_MODEL must not be empty")
    if not app_name:
        raise SettingsError("OPENROUTER_APP_NAME must not be empty")
    return Settings(
        api_key=_env_or_override("OPENROUTER_API_KEY", overrides),
        model=model,
        base_url=_validate_url(
            _env_or_override("OPENROUTER_BASE_URL", overrides, "https://openrouter.ai/api/v1"),
            "OPENROUTER_BASE_URL",
        ),
        site_url=_validate_url(
            _env_or_override("OPENROUTER_SITE_URL", overrides, "http://localhost:8501"),
            "OPENROUTER_SITE_URL",
        ),
        app_name=app_name,
        min_retrieval_score=_as_float(
            _env_or_override("MIN_RETRIEVAL_SCORE", overrides, "0.16"),
            "MIN_RETRIEVAL_SCORE",
            0.0,
            1.0,
        ),
        max_requests_per_session=_as_int(
            _env_or_override("MAX_REQUESTS_PER_SESSION", overrides, "30"),
            "MAX_REQUESTS_PER_SESSION",
            1,
            100_000,
        ),
        enable_dense_embeddings=_as_bool(
            _env_or_override("ENABLE_DENSE_EMBEDDINGS", overrides, "0"),
            "ENABLE_DENSE_EMBEDDINGS",
        ),
    )
