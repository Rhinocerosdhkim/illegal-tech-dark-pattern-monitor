"""Beweisakte — eine Seite, ein Vorgang, als PDF.

Die Ausgabe heisst bewusst nicht "Bericht". Die Verbraucherzentrale hat im
Seminar vom 19.08. das Wort "Beweisakte" benutzt, und der Unterschied ist
inhaltlich: Jeder Befund zeigt auf einen Screenshot, einen DOM-Hash und
einen Zeitpunkt. Was nicht belegt ist, steht nicht drin.

Aufbau:
    Kopf              Ziel, Erfassungsbedingungen, Reproduzierbarkeit
    Befundtabelle     die Uebersicht, aus der die Abmahnung entsteht
    je Befund         Norm, Tatbestand, Messwerte, Anspruchskette,
                      Herkunft der Schwellenwerte, Fehlalarmrisiken
    nicht pruefbar    was wir NICHT feststellen konnten, mit Begruendung
    Erfassungsprotokoll  Schritte mit Hash
    Hinweis           Haftungsabsicherung
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from dpm import PRODUKTNAME
from dpm.engine.conditions import MissingSignal, Signaltabelle
from dpm.engine.lauf import Lauf
from dpm.engine.rules import Regel
from dpm.engine.verdict import (EINDEUTIG, UNKLAR, VERDAECHTIG, Befund)

ANZEIGE = {EINDEUTIG: "eindeutig", VERDAECHTIG: "verdächtig",
           UNKLAR: "unklar", "unauffaellig": "unauffällig",
           "nicht_anwendbar": "nicht anwendbar"}

_PLATZHALTER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

# Das Regelwerk schreibt die Kategorien ohne Umlaute. In einem Dokument, das
# einer Abmahnung beiliegt, gehoert die richtige Schreibweise hin.
KATEGORIE = {"Irrefuehrung": "Irreführung", "Zeitdruck": "Zeitdruck",
             "Zwang": "Zwang", "Hindernisse": "Hindernisse"}

# Der verbindliche Wortlaut kommt aus Paket 3 des juristischen Teams. Bis
# dahin steht hier ein als vorlaeufig gekennzeichneter Text - lieber
# sichtbar unfertig als stillschweigend erfunden.
HINWEIS_VORLAEUFIG = (
    "PLATZHALTER — der verbindliche Wortlaut steht aus (Paket 3). "
    f"{PRODUKTNAME} stellt technisch messbare Tatsachen fest und ordnet sie "
    "einem Regelwerk zu. Es trifft keine rechtliche Feststellung eines "
    "Verstoßes. Die rechtliche Bewertung obliegt der prüfenden Person."
)


@dataclass
class Akte:
    html: Path
    pdf: Path | None
    anzahl_befunde: int


def erzeuge(lauf: Lauf, befunde: list, ausgabe: str | Path = "out",
            als_pdf: bool = True) -> Akte:
    ordner = Path(ausgabe) / lauf.run_id
    ordner.mkdir(parents=True, exist_ok=True)

    relevante = [b for b in befunde if b.berichtsrelevant]
    schritte = {s["schritt"]: s for s in lauf.schritte}

    for name in _screenshotnamen(relevante, lauf):
        quelle = lauf.screenshot(name)
        if quelle:
            shutil.copyfile(quelle, ordner / name)

    html = _umgebung().get_template("beweisakte.html").render(
        produkt=PRODUKTNAME,
        lauf=lauf,
        meta=lauf.meta,
        schritte=lauf.schritte,
        hinweis=HINWEIS_VORLAEUFIG,
        zusammenfassung=_zusammenfassung(befunde),
        eintraege=[_eintrag(nr, b, schritte, lauf)
                   for nr, b in enumerate(relevante, start=1)],
        kategorie=KATEGORIE,
    )

    ziel_html = ordner / "beweisakte.html"
    ziel_html.write_text(html, encoding="utf-8")

    pdf = _als_pdf(ziel_html) if als_pdf else None
    return Akte(html=ziel_html, pdf=pdf, anzahl_befunde=len(relevante))


# --- Aufbereitung --------------------------------------------------------

def _eintrag(nr: int, befund: Befund, schritte: dict, lauf: Lauf) -> dict:
    nachweise = [_nachweis(n, schritte, lauf) for n in befund.nachweise]
    return {
        "nr": nr,
        "regel": befund.regel,
        "stufe": ANZEIGE[befund.stufe],
        "stufe_code": befund.stufe,
        "bedingung": befund.bedingung,
        "begruendung": befund.begruendung,
        "herabgestuft": befund.herabgestuft,
        "hinweise": befund.hinweise,
        "unklar_wegen": befund.unklar_wegen,
        "nachweise": nachweise,
        "messwerte": ", ".join(f"{n['signal']} = {_kurz(n['wert'])}"
                               for n in nachweise) or "—",
        "screenshots": _bilder(nachweise),
        "erlaeuterung": _erlaeuterung(befund.regel, lauf.tabelle),
    }


def _nachweis(roh: dict, schritte: dict, lauf: Lauf) -> dict:
    schritt = schritte.get(roh.get("schritt")) or {}
    return {**roh,
            "anzeige": _kurz(roh.get("wert")),
            "url": schritt.get("url"),
            "dom_hash": schritt.get("dom_hash"),
            "zeitpunkt": lauf.meta.get("timestamp")}


def _bilder(nachweise: list) -> list:
    gesehen, bilder = set(), []
    for n in nachweise:
        datei = n.get("nachweis")
        if datei and datei.lower().endswith(".png") and datei not in gesehen:
            gesehen.add(datei)
            bilder.append({"datei": datei, "schritt": n.get("schritt"),
                           "dom_hash": n.get("dom_hash")})
    return bilder


def _erlaeuterung(regel: Regel, tabelle: Signaltabelle) -> str:
    """Setzt {signalname} durch den gemessenen Wert.

    Gefragt wird die vollstaendige Signaltabelle, nicht nur die Signale der
    zutreffenden Bedingung: Der Erlaeuterungstext nennt regelmaessig auch
    Messwerte, die den Befund nur einordnen.

    "[nicht erhoben]" steht ausschliesslich dort, wo tatsaechlich nichts
    gemessen wurde. In einem Dokument, das einer Abmahnung beiliegt, waere
    die Behauptung, etwas sei nicht erhoben worden, obwohl es vorliegt,
    ein Sachfehler.
    """
    if not regel.explanation_template_de:
        return ""

    def ersetze(treffer):
        try:
            return _kurz(tabelle.hole(treffer.group(1)))
        except MissingSignal:
            return "[nicht erhoben]"

    return _PLATZHALTER.sub(ersetze, regel.explanation_template_de)


def _zusammenfassung(befunde: list) -> list:
    zaehlung = {}
    for b in befunde:
        zaehlung[b.stufe] = zaehlung.get(b.stufe, 0) + 1
    reihenfolge = [EINDEUTIG, VERDAECHTIG, UNKLAR, "unauffaellig", "nicht_anwendbar"]
    return [{"stufe": ANZEIGE[s], "code": s, "anzahl": zaehlung[s]}
            for s in reihenfolge if zaehlung.get(s)]


def _screenshotnamen(befunde: list, lauf: Lauf) -> set:
    namen = {s.get("screenshot") for s in lauf.schritte if s.get("screenshot")}
    for b in befunde:
        namen.update(n.get("nachweis") for n in b.nachweise)
    return {n for n in namen if n and n.lower().endswith(".png")}


def _kurz(wert) -> str:
    if isinstance(wert, bool):
        return "ja" if wert else "nein"
    return str(wert)


def _umgebung() -> Environment:
    umgebung = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    umgebung.filters["absatz"] = lambda t: [a.strip() for a in (t or "").split("\n\n") if a.strip()]
    return umgebung


# --- PDF -----------------------------------------------------------------

def _als_pdf(html: Path) -> Path | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    ziel = html.with_suffix(".pdf")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        seite = browser.new_page()
        seite.goto(html.resolve().as_uri())
        seite.pdf(path=str(ziel), format="A4", print_background=True,
                  margin={"top": "18mm", "bottom": "18mm",
                          "left": "16mm", "right": "16mm"})
        browser.close()
    return ziel
