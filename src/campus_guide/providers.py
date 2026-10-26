"""Hosted generation provider for the OpenRouter-compatible chat endpoint."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .settings import Settings


class ProviderError(RuntimeError):
    """Raised when the hosted model cannot return a usable completion."""


@dataclass(frozen=True)
class GenerationResponse:
    text: str
    model: str


class OpenRouterProvider:
    """Minimal standard-library client for OpenRouter's chat-completions API."""

    name = "OpenRouter"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return self.settings.api_configured

    def generate(self, system_prompt: str, user_prompt: str) -> GenerationResponse:
        if not self.configured:
            raise ProviderError("OPENROUTER_API_KEY is not configured")
        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 320,
        }
        try:
            request = urllib.request.Request(
                f"{self.settings.base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.settings.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": self.settings.site_url,
                    "X-Title": self.settings.app_name,
                },
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=35) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:240]
            raise ProviderError(f"OpenRouter returned HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"OpenRouter connection failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise ProviderError("OpenRouter timed out after 35 seconds") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("OpenRouter returned invalid JSON") from exc
        except (OSError, ValueError) as exc:
            raise ProviderError(f"OpenRouter request failed: {exc}") from exc

        try:
            choices = body["choices"]
            if not isinstance(choices, list) or not choices:
                raise TypeError("choices must be a non-empty list")
            message = choices[0]["message"]
            if not isinstance(message, dict):
                raise TypeError("message must be an object")
            raw_content = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("OpenRouter response did not contain assistant content") from exc

        if isinstance(raw_content, list):
            text_parts = [
                part["text"]
                for part in raw_content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
            text = "".join(text_parts).strip()
        elif isinstance(raw_content, str):
            text = raw_content.strip()
        else:
            raise ProviderError("OpenRouter assistant content had an unsupported shape")
        if not text:
            raise ProviderError("OpenRouter returned an empty answer")
        model = body.get("model", self.settings.model)
        return GenerationResponse(text=text, model=model if isinstance(model, str) else self.settings.model)


def build_provider(settings: Settings) -> OpenRouterProvider | None:
    """Return a configured provider, or None for the reproducible keyless path."""

    provider = OpenRouterProvider(settings)
    return provider if provider.configured else None
