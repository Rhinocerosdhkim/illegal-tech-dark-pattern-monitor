"""The one place a language model is called from."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional, Any

# Cheapest vision-capable tier.
DEFAULT_MODEL = "gemini-3.5-flash-lite"


class ModelError(Exception):
    """The model call failed or the answer was unusable."""


def unavailable() -> str | None:
    """Why the model cannot be called, or None if it can."""
    try:
        import google.genai  # noqa: F401
    except ImportError:
        return ("the google-genai package is missing "
                "(.venv/bin/pip install google-genai)")
    if os.environ.get("DPM_VERTEX"):
        if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
            return ("DPM_VERTEX is set but GOOGLE_CLOUD_PROJECT is not. "
                    "Run: gcloud config set project <ID>")
        return None
    if not os.environ.get("GEMINI_API_KEY"):
        return ("neither GEMINI_API_KEY nor DPM_VERTEX + "
                "GOOGLE_CLOUD_PROJECT is set")
    return None


@dataclass
class Model:
    """A model, bound to whichever backend the environment selected."""

    name: str
    backend: str
    _client: object

    @classmethod
    def open(cls) -> "Model":
        reason = unavailable()
        if reason:
            raise ModelError(reason)

        from google import genai

        name = os.environ.get("DPM_MODEL", DEFAULT_MODEL)
        if os.environ.get("DPM_VERTEX"):
            client = genai.Client(
                vertexai=True,
                project=os.environ["GOOGLE_CLOUD_PROJECT"],
                location=os.environ.get("GOOGLE_CLOUD_LOCATION",
                                        "europe-west4"))
            return cls(name=name, backend="vertex", _client=client)

        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ModelError("GEMINI_API_KEY is missing from environment")

        client = genai.Client(api_key=key)
        return cls(name=name, backend="ai-studio", _client=client)

    async def ask(self, prompt: str, schema: dict,
                  screenshot: bytes | None = None,
                  history: List[Any] | None = None,
                  system_instruction: str | None = None) -> dict:
        """One structured call. Returns the parsed answer as a dict."""
        from google.genai import types

        parts = []
        if screenshot is not None:
            parts.append(types.Part.from_bytes(data=screenshot,
                                               mime_type="image/png"))
        parts.append(types.Part.from_text(text=prompt))

        contents = list(history) if history else []
        contents.append(types.Content(role="user", parts=parts))

        try:
            response = await self._client.aio.models.generate_content(
                model=self.name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1))
        except Exception as error:                      # SDK, network, quota
            raise ModelError(f"{type(error).__name__}: {error}") from error

        text = getattr(response, "text", None)
        if not text:
            raise ModelError("the model returned no text")

        try:
            answer = json.loads(text)
        except json.JSONDecodeError as error:
            raise ModelError(f"answer was not JSON: {error}") from error

        if not isinstance(answer, dict):
            raise ModelError(f"expected an object, got {type(answer).__name__}")
        return answer
