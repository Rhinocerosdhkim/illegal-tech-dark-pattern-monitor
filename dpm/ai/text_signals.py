"""AI 1 -- reading the signals a screenshot can honestly show.

Only signals that exist in rules/_SIGNALE.md may be produced, and only ones
a rendered page really shows: is there a countdown, what does it say, does a
scarcity note name a number, is VAT mentioned. Everything the eye cannot
measure -- button areas in px2, WCAG contrast ratios, cookies set before
consent -- is deliberately absent here. Those belong in
dpm/signals/extractors.js and a model guessing them from an image would only
produce confident nonsense.

Two rules from the contract are enforced here rather than asked for politely
in the prompt:

    Value and confidence (ARBEITSTEILUNG_Technik.md 2.8). Below the
    threshold the signal goes to signal_errors, not into signals.

    A value we could not read is never 0, false or "". scarcity_value on
    "nur noch wenige verfuegbar" has no number, so it goes to signal_errors.
    Reporting 0 would mean "measured, zero left" and a rule would fire on it.

The model answers every value as a string. That avoids the JSON-Schema union
that Gemini structured output supports only partially, and it leaves the
typing here, where a mismatch can be turned into a signal_error instead of a
silent coercion.
"""

from __future__ import annotations

import os

from .client import Model, ModelError

# What may be read from an image, and as what. Names are exactly the ones
# from rules/_SIGNALE.md -- a name that is not in here cannot reach a rule.
SIGNAL_TYPES = {
    "countdown_element_present": bool,
    "countdown_text": str,
    "scarcity_text_present": bool,
    "scarcity_value": int,
    "viewer_count_present": bool,
    "vat_disclosure_present": bool,
    "gratis_claim_present": bool,
    "has_price_display": bool,
    "order_button_found": bool,
    "order_button_label": str,
}

DEFAULT_CONFIDENCE = 0.7

_PROMPT = """Read the following from this screenshot of a German web shop.

{wanted}

Rules:
- Answer every value as a string: "true" / "false" for yes-or-no, digits for
  a number, the literal wording for text.
- confidence is 0.0 to 1.0 -- how sure you are of that value.
- If something cannot be read from this image, leave it out of "signals" and
  put it in "not_readable" with an English reason. Never guess, and never
  answer 0 or false for something you could not check. "nur noch wenige
  verfuegbar" has no number, so scarcity_value is not readable there.
- Text values are quoted verbatim from the page, in German, not translated."""

_DESCRIPTIONS = {
    "countdown_element_present": "is a running countdown visible",
    "countdown_text": "the text around the countdown, verbatim",
    "scarcity_text_present": "is there a scarcity note (\"nur noch 2 verfuegbar\")",
    "scarcity_value": "the number of items that note names",
    "viewer_count_present": "a note like \"17 Personen sehen sich das gerade an\"",
    "vat_disclosure_present": "a VAT note near the price (\"inkl. MwSt.\")",
    "gratis_claim_present": "advertising with gratis / kostenlos / umsonst",
    "has_price_display": "is a price shown at all",
    "order_button_found": "is there a button that completes a paid order",
    "order_button_label": "that button's label, verbatim",
}


def _schema(wanted) -> dict:
    name = {"type": "string", "enum": list(wanted)}
    return {
        "type": "object",
        "properties": {
            "signals": {"type": "array", "items": {
                "type": "object",
                "properties": {"name": name, "value": {"type": "string"},
                               "confidence": {"type": "number"}},
                "required": ["name", "value", "confidence"]}},
            "not_readable": {"type": "array", "items": {
                "type": "object",
                "properties": {"name": name, "reason": {"type": "string"}},
                "required": ["name", "reason"]}},
        },
        "required": ["signals", "not_readable"],
    }


def _typed(name: str, raw: str):
    """Raw string -> the type the signal list promises. None if it does not fit."""
    wanted = SIGNAL_TYPES[name]
    text = str(raw).strip()

    if wanted is bool:
        if text.lower() in ("true", "yes", "ja"):
            return True
        if text.lower() in ("false", "no", "nein"):
            return False
        return None
    if wanted is int:
        try:
            return int(text)
        except ValueError:
            return None
    return text or None


async def read(model: Model, screenshot: bytes, wanted=None):
    """Read signals off one screenshot.

    Returns (values, errors): {name: value} and {name: why not measured}.
    The step and the screenshot are stamped on by the caller -- asking the
    model for them would put the evidence binding at the mercy of the
    prompt being followed.
    """
    wanted = list(wanted or SIGNAL_TYPES)
    unknown = [n for n in wanted if n not in SIGNAL_TYPES]
    if unknown:
        raise ValueError(f"not in SIGNAL_TYPES: {unknown}")

    threshold = float(os.environ.get("DPM_MIN_CONFIDENCE", DEFAULT_CONFIDENCE))
    listing = "\n".join(f"- {n}: {_DESCRIPTIONS[n]}" for n in wanted)
    answer = await model.ask(_PROMPT.format(wanted=listing),
                             schema=_schema(wanted), screenshot=screenshot)

    values, errors = {}, {}
    seen = set()

    for entry in answer.get("signals") or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if name not in wanted or name in seen:
            continue
        seen.add(name)

        confidence = entry.get("confidence")
        if not isinstance(confidence, (int, float)) or confidence < threshold:
            errors[name] = (f"model was not certain enough "
                            f"(confidence {confidence}, needed {threshold})")
            continue

        value = _typed(name, entry.get("value"))
        if value is None:
            errors[name] = (f"model answered {entry.get('value')!r}, which is "
                            f"not a {SIGNAL_TYPES[name].__name__}")
            continue
        values[name] = value

    for entry in answer.get("not_readable") or []:
        if isinstance(entry, dict) and entry.get("name") in wanted:
            seen.add(entry["name"])
            errors.setdefault(entry["name"],
                              str(entry.get("reason") or "not readable"))

    for name in wanted:
        if name not in seen:
            errors.setdefault(name, "the model did not answer for this signal")

    return values, errors
