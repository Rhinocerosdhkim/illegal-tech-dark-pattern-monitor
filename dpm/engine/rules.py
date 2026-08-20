"""Regelwerk laden und vereinheitlichen.

Die Regeldateien sind von Hand geschrieben und liegen derzeit in zwei
Schreibweisen vor (siehe docs/ABSTIMMUNG_Regelwerk.md). Die Engine nimmt
beide an und normalisiert sie hier an einer Stelle.

Das ist Absicht: Das juristische Team soll seine Dateien inhaltlich
verbessern koennen, ohne auf eine Formatabstimmung zu warten — und wir
sollen nicht blockiert sein, waehrend die Abstimmung laeuft.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

WURZEL = Path(__file__).resolve().parents[2]

STUFEN = ("eindeutig", "verdaechtig")


@dataclass
class Bedingung:
    text: str
    begruendung: str | None = None


@dataclass
class Regel:
    id: str
    name_de: str
    kategorie: str
    status: str
    datei: str
    legal_basis: list = field(default_factory=list)
    tatbestand_de: str = ""
    anspruchskette: str = ""
    applies_when: dict = field(default_factory=dict)   # all / any / none
    verdict_rules: dict = field(default_factory=dict)  # Stufe -> [Bedingung]
    listen: dict = field(default_factory=dict)         # benannte Wortlisten
    explanation_template_de: str = ""
    threshold_source: str = ""
    false_positive_risks: list = field(default_factory=list)
    menschliche_pruefung: list = field(default_factory=list)
    disclaimer_required: bool = True

    @property
    def norm(self) -> str:
        """Erste Fundstelle — das, was in der Befundtabelle steht."""
        return self.legal_basis[0] if self.legal_basis else "—"


def lade_regelwerk(verzeichnis: str | Path | None = None) -> list:
    """Laedt rules/*.yaml.

    Der Standardpfad haengt bewusst nicht am Arbeitsverzeichnis: Wird das
    Werkzeug von woanders aufgerufen, faende glob() nichts, es wuerden null
    Regeln geladen und die Beweisakte meldete kommentarlos "0 Befunde" -
    das gefaehrlichste denkbare Ergebnis.
    """
    verzeichnis = Path(verzeichnis) if verzeichnis else WURZEL / "rules"
    regeln = []
    for datei in sorted(verzeichnis.glob("*.yaml")):
        if datei.name.startswith("_"):        # _VORLAGE.yaml ist keine Regel
            continue
        inhalt = yaml.safe_load(datei.read_text(encoding="utf-8"))
        for roh in inhalt if isinstance(inhalt, list) else [inhalt]:
            if isinstance(roh, dict) and roh.get("id"):
                regeln.append(_baue(roh, datei.name))
    if not regeln:
        raise FileNotFoundError(
            f"In {verzeichnis} steht keine einzige Regel. Ohne Regelwerk kann "
            f"nichts geprueft werden.")
    return regeln


def _baue(roh: dict, dateiname: str) -> Regel:
    return Regel(
        id=roh["id"],
        name_de=roh.get("name_de", roh["id"]),
        kategorie=roh.get("kategorie", "—"),
        status=roh.get("status", "ENTWURF"),
        datei=dateiname,
        legal_basis=list(roh.get("legal_basis") or []),
        tatbestand_de=(roh.get("tatbestand_de") or "").strip(),
        anspruchskette=(roh.get("anspruchskette") or "").strip(),
        applies_when=_applies_when(roh.get("applies_when")),
        verdict_rules=_verdict_rules(roh.get("verdict_rules")),
        listen=_listen(roh.get("listen")),
        explanation_template_de=(roh.get("explanation_template_de") or "").strip(),
        threshold_source=(roh.get("threshold_source") or "").strip(),
        false_positive_risks=[str(r).strip() for r in (roh.get("false_positive_risks") or [])],
        menschliche_pruefung=list(roh.get("menschliche_pruefung") or []),
        disclaimer_required=bool(roh.get("disclaimer_required", True)),
    )


def _applies_when(roh) -> dict:
    """Flache Liste und all/any/none-Form auf eine Struktur bringen."""
    leer = {"all": [], "any": [], "none": []}
    if not roh:
        return leer
    if isinstance(roh, list):
        return {**leer, "all": [str(b) for b in roh]}
    return {schluessel: [str(b) for b in (roh.get(schluessel) or [])]
            for schluessel in leer}


def _listen(roh) -> dict:
    """Benannte Wortlisten fuer die Operatoren 'in' und 'not in'.

    Damit pflegt das juristische Team zulaessige und unzulaessige
    Beschriftungen, ohne dass jemand programmiert (_VORLAGE.yaml, LISTEN).
    """
    if not isinstance(roh, dict):
        return {}
    return {name: [str(e) for e in (eintraege or [])]
            for name, eintraege in roh.items()}


def _verdict_rules(roh) -> dict:
    """Zeichenketten- und Objektform annehmen.

    'severity' wird bewusst ignoriert: eine zweite Schwereskala neben
    eindeutig/verdaechtig/unklar waere eine Fehlerquelle und muesste in der
    Praesentation zusaetzlich verteidigt werden (ABSTIMMUNG_Regelwerk.md §2).
    'reason' wird uebernommen — eine Begruendung je Bedingung ist fuer die
    Beweisakte wertvoll.
    """
    ergebnis = {stufe: [] for stufe in STUFEN}
    for stufe in STUFEN:
        for eintrag in (roh or {}).get(stufe) or []:
            if isinstance(eintrag, dict):
                ergebnis[stufe].append(Bedingung(
                    text=str(eintrag.get("condition", "")),
                    begruendung=(eintrag.get("reason") or "").strip() or None))
            else:
                ergebnis[stufe].append(Bedingung(text=str(eintrag)))
    return ergebnis
