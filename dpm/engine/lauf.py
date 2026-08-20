"""Einen Erfassungslauf einlesen.

Eingang der Auswertungsschicht. Alles, was von hier an passiert, kennt nur
noch capture.json und das Zielprofil — nie einen Browser. Deshalb laesst
sich die gesamte Auswertung gegen eine handgeschriebene Fixture entwickeln,
ohne auf die Erfassungsschicht zu warten.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .conditions import Signaltabelle


@dataclass
class Lauf:
    pfad: Path
    meta: dict
    schritte: list
    tabelle: Signaltabelle
    ziel: dict = field(default_factory=dict)

    @property
    def run_id(self) -> str:
        return self.meta.get("run_id", self.pfad.name)

    @property
    def branche(self) -> str:
        return self.meta.get("branche") or self.ziel.get("branche") or "—"

    def screenshot(self, dateiname: str) -> Path | None:
        if not dateiname:
            return None
        datei = self.pfad / dateiname
        return datei if datei.exists() else None


def lade_lauf(pfad: str | Path, zielverzeichnis: str | Path = "data/targets") -> Lauf:
    pfad = Path(pfad)
    datei = pfad / "capture.json" if pfad.is_dir() else pfad
    roh = json.loads(datei.read_text(encoding="utf-8"))

    meta = roh.get("meta", {})
    werte = dict(roh.get("signals") or {})
    fehler = dict(roh.get("signal_errors") or {})

    ziel = _lade_zielprofil(meta.get("ziel"), zielverzeichnis)

    # Vom Menschen bestaetigte Voraussetzungen (C4). Sie sind zugleich Wert
    # und Feststellung — und tragen als Nachweis den Namen der Datei, in der
    # jemand sie bestaetigt hat.
    bestaetigt = set()
    for name, wert in (ziel.get("bestaetigt_durch_mensch") or {}).items():
        werte[name] = {"wert": wert, "schritt": "Zielprofil",
                       "nachweis": f"targets/{meta.get('ziel')}.yaml"}
        fehler.pop(name, None)
        bestaetigt.add(name)

    return Lauf(pfad=datei.parent, meta=meta, schritte=roh.get("schritte") or [],
                ziel=ziel,
                tabelle=Signaltabelle(werte=werte, fehler=fehler, bestaetigt=bestaetigt))


def _lade_zielprofil(name: str | None, verzeichnis: str | Path) -> dict:
    if not name:
        return {}
    datei = Path(verzeichnis) / f"{name}.yaml"
    if not datei.exists():
        return {}
    return yaml.safe_load(datei.read_text(encoding="utf-8")) or {}
