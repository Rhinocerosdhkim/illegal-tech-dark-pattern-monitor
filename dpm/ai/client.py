"""The one place a language model is called from.

Two backends, one call site. Which one is used depends on the environment
only, never on the calling code:

    DPM_VERTEX=1 + GOOGLE_CLOUD_PROJECT   Vertex AI. Billed through Google
                                          Cloud, so the hackathon credits
                                          apply here.
    GEMINI_API_KEY                        Gemini API in AI Studio. Free tier,
                                          roughly 10-15 requests per minute.

Why that distinction is in the code at all: the 300 USD Google Cloud credit
explicitly excludes "Gemini API in AI Studio" and covers Vertex AI. Models,
SDK and every call below are identical between the two, so the choice stays
one environment variable and nobody has to touch the capture code on the
morning of the presentation.

No response_schema is built from a class here. The schema is a plain dict
(see ai/schemas.py) and the answer is checked by hand, for the same reason
the condition parser does not use eval(): a wrong value has to produce a
readable message, not a coercion nobody notices. A measurement we could not
read belongs in signal_errors, never in signals.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

# Cheapest vision-capable tier. The two tasks we use a model for -- "which
# numbered box do I click" and "is there a countdown" -- need no reasoning
# ability, so paying for a larger model buys nothing.
DEFAULT_MODEL = "gemini-2.5-flash-lite"


class ModelError(Exception):
    """The model call failed or the answer was unusable.

    Always caught by the caller and turned into a signal_error. It never
    aborts a capture: a partial capture is still evidence.
    """


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

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        return cls(name=name, backend="ai-studio", _client=client)

    async def ask(self, prompt: str, schema: dict,
                  screenshot: bytes | None = None) -> dict:
        """One structured call. Returns the parsed answer as a dict.

        Async on purpose. The capture layer drives Playwright over a
        websocket; a synchronous model call inside the event loop stalls
        that connection for the whole round trip and surfaces later as an
        unexplained "Target closed".
        """
        from google.genai import types

        parts = []
        if screenshot is not None:
            parts.append(types.Part.from_bytes(data=screenshot,
                                               mime_type="image/png"))
        parts.append(prompt)

        try:
            response = await self._client.aio.models.generate_content(
                model=self.name,
                contents=parts,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.1))
        except Exception as error:                      # SDK, network, quota
            raise ModelError(f"{type(error).__name__}: {error}") from error

        text = getattr(response, "text", None)
        if not text:
            # Empty happens on a safety block or when the answer hit the
            # token limit. Both are "not measured", not "measured as absent".
            raise ModelError("the model returned no text")

        try:
            answer = json.loads(text)
        except json.JSONDecodeError as error:
            raise ModelError(f"answer was not JSON: {error}") from error

        if not isinstance(answer, dict):
            raise ModelError(f"expected an object, got {type(answer).__name__}")
        return answer
