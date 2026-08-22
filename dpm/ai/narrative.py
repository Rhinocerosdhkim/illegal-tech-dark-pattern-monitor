"""AI ④ — the German prose under a finding.

The model describes, it does not decide. The verdict level, the rule and
the measured values are all fixed before this is called; the only thing
asked of the model is to put them into a sentence a lawyer can read.

That still puts machine-written text into a document which may be
attached to a formal warning letter, so nothing here is trusted. Every
answer is checked against the facts it was given and dropped whole if it
does not hold up:

* every number in the text must be one we measured,
* every signal name must be one that exists,
* it may not assert a violation — that is the reader's finding, not ours,
* and it has to stay short.

A dropped answer is not an error. The Beweisakte is complete without it;
the deterministic explanation from the rulebook carries the finding.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .client import Model, ModelError

# Words that turn a description into a legal conclusion. The tool states
# facts and points at a provision; whether that is a violation is decided
# by the person reading the file (docs/DECISIONS.md, 19.08.).
FORBIDDEN = ("verstoß", "verstoss", "verstößt", "verstoesst", "rechtswidrig",
             "illegal", "unzulässig", "unzulaessig", "abmahnfähig",
             "abmahnfaehig", "strafbar", "eindeutig rechtswidrig")

MAX_CHARS = 700

_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_SNAKE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")

SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string"}},
    "required": ["text"],
}

PROMPT = """Formuliere zu einem technischen Befund zwei bis drei Sätze auf Deutsch.

Regeln:
- Beschreibe ausschließlich die unten genannten Messwerte. Erfinde keine Zahl
  und keinen Wert, der nicht dasteht.
- Stelle keinen Rechtsverstoß fest. Nenne die Norm nur als das, woran gemessen
  wurde.
- Sachlich, keine Wertung, keine Empfehlung, kein Konjunktiv der Empörung.
- Höchstens {max_chars} Zeichen.

Befund: {rule_id} — {rule_name}
Stufe: {level}
Herangezogene Norm: {norm}
Gemessen wurde:
{measurements}
"""


@dataclass
class Draft:
    text: str | None
    rejected: str | None = None      # why it was dropped, for the log


def _show(value) -> str:
    """A value as the document writes it — same rule as the Beweisakte."""
    if isinstance(value, bool):
        return "ja" if value else "nein"
    return str(value)


def facts(finding, level_label: str) -> dict:
    """The values a summary may mention. Nothing else may appear."""
    return {
        "rule_id": finding.rule.id,
        "rule_name": finding.rule.name,
        "norm": finding.rule.norm or "",
        "level": level_label,
        "measurements": [(e["signal"], _show(e.get("value")))
                         for e in finding.evidence],
    }


def check(text: str, given: dict) -> Draft:
    """Hold the answer against the facts it was given."""
    text = (text or "").strip()
    if not text:
        return Draft(None, "leer")
    if len(text) > MAX_CHARS:
        return Draft(None, f"zu lang ({len(text)} Zeichen)")

    lowered = text.lower()
    for word in FORBIDDEN:
        if word in lowered:
            return Draft(None, f"stellt einen Verstoß fest („{word}“)")

    allowed_numbers = set()
    allowed_names = set()
    for name, value in given["measurements"]:
        allowed_names.add(name)
        allowed_numbers.update(_NUMBER.findall(value))
    # The provision and the rule id carry digits of their own.
    for source in (given["norm"], given["rule_id"], given["rule_name"]):
        allowed_numbers.update(_NUMBER.findall(source))

    invented = {n for n in _NUMBER.findall(text)
                if n not in allowed_numbers
                and n.replace(",", ".") not in allowed_numbers}
    if invented:
        return Draft(None, f"nennt nicht gemessene Zahlen: {sorted(invented)}")

    unknown = {s for s in _SNAKE.findall(text) if s not in allowed_names}
    if unknown:
        return Draft(None, f"nennt unbekannte Signale: {sorted(unknown)}")

    return Draft(text)


async def summarise(model: Model, given: dict) -> Draft:
    """Ask for one summary and return it only if it survives the check."""
    lines = "\n".join(f"- {name} = {value}"
                      for name, value in given["measurements"]) or "- (nichts)"
    prompt = PROMPT.format(max_chars=MAX_CHARS, measurements=lines,
                           rule_id=given["rule_id"],
                           rule_name=given["rule_name"],
                           level=given["level"], norm=given["norm"])
    try:
        answer = await model.ask(prompt, SCHEMA)
    except ModelError as error:
        return Draft(None, str(error))
    return check(answer.get("text", ""), given)
