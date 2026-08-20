"""Einen Erfassungslauf einlesen.

Eingang der Auswertungsschicht. Alles, was von hier an passiert, kennt nur
noch capture.json und das Zielprofil — nie einen Browser. Deshalb laesst
sich die gesamte Auswertung gegen eine handgeschriebene Fixture entwickeln,
ohne auf die Erfassungsschicht zu warten.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .conditions import Signaltabelle

WURZEL = Path(__file__).resolve().parents[2]
_SICHERER_NAME = re.compile(r"^[\w.\-]+$")


@dataclass
class Lauf:
    pfad: Path
    meta: dict
    schritte: list
    tabelle: Signaltabelle
    ziel: dict = field(default_factory=dict)
    warnungen: list = field(default_factory=list)

    @property
    def run_id(self) -> str:
        roh = str(self.meta.get("run_id") or self.pfad.name)
        # Der Wert kommt aus capture.json und wird zu einem Ordnernamen.
        # Er darf das Ausgabeverzeichnis nicht verlassen.
        if _SICHERER_NAME.match(roh):
            return roh
        return re.sub(r"[^\w.\-]", "_", roh).lstrip(".") or "lauf"

    @property
    def branche(self) -> str:
        return self.meta.get("branche") or self.ziel.get("branche") or "—"

    def screenshot(self, dateiname: str) -> Path | None:
        if not dateiname:
            return None
        datei = self.pfad / dateiname
        return datei if datei.exists() else None


def lade_lauf(pfad: str | Path, zielverzeichnis: str | Path | None = None) -> Lauf:
    pfad = Path(pfad)
    datei = pfad / "capture.json" if pfad.is_dir() else pfad
    roh = json.loads(datei.read_text(encoding="utf-8"))

    warnungen: list = []
    meta = roh.get("meta") or {}
    fehler = {k: str(v) for k, v in (roh.get("signal_errors") or {}).items()}
    werte = _signale(roh.get("signals"), fehler, warnungen)
    schritte = _schritte(roh.get("schritte"), warnungen)

    ziel = _lade_zielprofil(meta.get("ziel"),
                            zielverzeichnis or WURZEL / "data" / "targets",
                            warnungen)

    # Vom Menschen bestaetigte Voraussetzungen (C4). Sie sind zugleich Wert
    # und Feststellung — und tragen als Nachweis den Namen der Datei, in der
    # jemand sie bestaetigt hat.
    bestaetigt = set()
    for name, wert in (ziel.get("bestaetigt_durch_mensch") or {}).items():
        werte[name] = {"wert": wert, "schritt": "Zielprofil",
                       "nachweis": f"{meta.get('ziel')}.yaml"}
        fehler.pop(name, None)
        bestaetigt.add(name)

    return Lauf(pfad=datei.parent, meta=meta, schritte=schritte, ziel=ziel,
                warnungen=warnungen,
                tabelle=Signaltabelle(werte=werte, fehler=fehler, bestaetigt=bestaetigt))


def _signale(roh, fehler: dict, warnungen: list) -> dict:
    """Signale einlesen und die Form des Vertrags durchsetzen.

    Erwartet wird je Signal {"wert", "schritt", "nachweis"}. Ein blanker Wert
    ist laut AGENDA_Technik.md 2.1 unzulaessig - er laesst sich spaeter nicht
    an ein Beweismittel binden. Wir brechen deswegen aber nicht ab: am
    Dienstag steht kein Entwickler bereit. Stattdessen wird der Wert
    uebernommen, der fehlende Nachweis vermerkt und laut gemeldet.

    "null" wandert nach signal_errors. null heisst nicht "gemessen und leer",
    sondern "nicht gemessen" - und das ist juristisch eine ganz andere
    Aussage.
    """
    werte = {}
    for name, eintrag in (roh or {}).items():
        if isinstance(eintrag, dict) and "wert" in eintrag:
            if eintrag["wert"] is None:
                fehler.setdefault(name, "Wert war null — als nicht erhoben gewertet")
                warnungen.append(f"Signal '{name}' hatte den Wert null und gilt "
                                 f"als nicht erhoben.")
                continue
            werte[name] = eintrag
            continue
        if eintrag is None:
            fehler.setdefault(name, "Wert war null — als nicht erhoben gewertet")
            warnungen.append(f"Signal '{name}' hatte den Wert null und gilt "
                             f"als nicht erhoben.")
            continue
        warnungen.append(
            f"Signal '{name}' kam ohne Nachweis an (erwartet: "
            f"{{wert, schritt, nachweis}}). Der Befund laesst sich nicht an "
            f"einen Screenshot binden.")
        werte[name] = {"wert": eintrag, "schritt": None, "nachweis": None}
    return werte


def _schritte(roh, warnungen: list) -> list:
    schritte = []
    for eintrag in roh or []:
        if isinstance(eintrag, dict) and eintrag.get("schritt"):
            schritte.append(eintrag)
        else:
            warnungen.append(f"Schritt ohne Bezeichnung uebergangen: {eintrag!r}")
    return schritte


def _lade_zielprofil(name, verzeichnis, warnungen: list) -> dict:
    if not name:
        return {}
    if not _SICHERER_NAME.match(str(name)):
        warnungen.append(f"Zielname {name!r} ist kein einfacher Dateiname — "
                         f"kein Zielprofil geladen.")
        return {}
    datei = Path(verzeichnis) / f"{name}.yaml"
    if not datei.exists():
        warnungen.append(
            f"Kein Zielprofil {datei.name} gefunden. Ohne menschliche "
            f"Bestaetigung bleibt jede Regel, deren Anwendbarkeit auf einer "
            f"Ableitung beruht, auf 'verdaechtig' begrenzt (C4).")
        return {}
    inhalt = yaml.safe_load(datei.read_text(encoding="utf-8"))
    if not isinstance(inhalt, dict):
        warnungen.append(f"{datei.name} enthaelt kein Zielprofil — uebergangen.")
        return {}
    bestaetigt = inhalt.get("bestaetigt_durch_mensch")
    if bestaetigt is not None and not isinstance(bestaetigt, dict):
        warnungen.append(f"{datei.name}: 'bestaetigt_durch_mensch' muss "
                         f"Signalname: Wert enthalten — uebergangen.")
        inhalt["bestaetigt_durch_mensch"] = {}
    return inhalt
