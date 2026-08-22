"""AI ② — a document with links becomes a target list.

The agency does not keep its candidates in a YAML file; it keeps them in
a spreadsheet or a Word document that grew over months. This reads such a
file, pulls the addresses out and proposes an industry for each — because
without `branche` there is no statistic by industry later, and the
seminar asked for exactly that.

The model reads the text; it does not get to invent entries. Every
address it returns has to occur in the document verbatim, otherwise the
row is dropped. An industry it makes up is discarded on its own, but the
address survives: a missing industry is a blank a person fills in, an
invented address is a site nobody asked us to visit.

Text extraction is stdlib only. XLSX and DOCX are zip archives of XML,
and all we need out of them is the text — that is not worth two more
dependencies on the day of the feature freeze.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from pathlib import Path

from .client import Model, ModelError

# The industries in use. The list is short on purpose: it is the axis of
# the statistic in the market overview, and a free-text field there means
# "Mode" and "Bekleidung" become two industries.
INDUSTRIES = ["Ticketing", "Reise", "Mode", "Telekommunikation", "Möbel",
              "Elektronik", "Medien", "Finanzen", "Lebensmittel"]

MAX_CHARS = 20000

_HOST = re.compile(r"[a-z0-9][a-z0-9.-]*\.[a-z]{2,}", re.IGNORECASE)
_XML_TAG = re.compile(r"<[^>]+>")

SCHEMA = {
    "type": "object",
    "properties": {
        "targets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "branche": {"type": "string", "enum": INDUSTRIES},
                },
                "required": ["url", "branche"],
            },
        }
    },
    "required": ["targets"],
}

PROMPT = """Aus dem folgenden Dokument sollen Prüfziele werden.

Gib jede Webadresse zurück, die im Dokument steht, und schlage je Adresse
eine Branche vor. Zulässig sind ausschließlich: {industries}.

Regeln:
- Nur Adressen, die wörtlich im Dokument stehen. Erfinde keine.
- Jede Adresse nur einmal.
- Keine Adressen von Behörden, Gesetzestexten oder Nachschlagewerken —
  gemeint sind Angebote von Unternehmen an Verbraucher.

Dokument:
{document}
"""


def text_of(path: str | Path) -> str:
    """The readable text of a csv, txt, xlsx or docx file."""
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in (".csv", ".txt", ".md", ".tsv"):
        return path.read_text(encoding="utf-8-sig", errors="replace")

    if suffix in (".xlsx", ".xlsm", ".docx"):
        parts = []
        with zipfile.ZipFile(path) as archive:
            wanted = [n for n in archive.namelist()
                      if n.endswith(("sharedStrings.xml", "document.xml"))
                      or "/worksheets/" in n and n.endswith(".xml")]
            for name in wanted:
                raw = archive.read(name).decode("utf-8", errors="replace")
                parts.append(_XML_TAG.sub(" ", raw))
        return " ".join(parts)

    raise ValueError(f"Dateiformat {suffix or '(ohne Endung)'} wird nicht "
                     f"gelesen — csv, txt, xlsx oder docx")


def host(value: str) -> str:
    """The bare host of an address, for comparing against the document."""
    found = _HOST.search((value or "").replace("://", " "))
    if not found:
        return ""
    name = found.group(0).lower()
    # Not lstrip("www."): that strips characters, not a prefix, and would
    # turn "wow-shop.de" into "ow-shop.de".
    return name[4:] if name.startswith("www.") else name


def verify(candidates: list, document: str) -> tuple[list, list]:
    """Keep what the document actually contains; report the rest.

    Matched by host rather than by exact string: a table often carries
    `viagogo.de` where the model answers `https://www.viagogo.de`, and
    that is the same target, not an invention.
    """
    haystack = document.lower()
    kept, dropped, seen = [], [], set()
    for entry in candidates:
        name = host(entry.get("url", ""))
        if not name:
            dropped.append({**entry, "grund": "keine lesbare Adresse"})
            continue
        if name in seen:
            continue
        if name not in haystack:
            dropped.append({**entry, "grund": "steht nicht im Dokument"})
            continue
        seen.add(name)
        branche = entry.get("branche")
        kept.append({"url": entry.get("url", "").strip(),
                     "host": name,
                     "branche": branche if branche in INDUSTRIES else ""})
    return kept, dropped


async def read_targets(model: Model, path: str | Path) -> tuple[list, list]:
    """Read one document and return (usable targets, dropped entries)."""
    document = text_of(path)[:MAX_CHARS]
    prompt = PROMPT.format(industries=" · ".join(INDUSTRIES),
                           document=document)
    try:
        answer = await model.ask(prompt, SCHEMA)
    except ModelError as error:
        raise ModelError(f"Zielliste konnte nicht gelesen werden: {error}")

    candidates = answer.get("targets")
    if not isinstance(candidates, list):
        raise ModelError("die Antwort enthielt keine Zielliste")
    return verify(candidates, document)


def write(targets: list, path: str | Path) -> Path:
    """Write the list a person then corrects."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["url", "branche",
                                                    "geprueft_von_mensch"])
        writer.writeheader()
        for target in targets:
            writer.writerow({"url": target["url"],
                             "branche": target["branche"],
                             "geprueft_von_mensch": "nein"})
    return path
