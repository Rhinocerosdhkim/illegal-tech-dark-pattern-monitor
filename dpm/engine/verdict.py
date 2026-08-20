"""Vom Messwert zur Befundstufe.

    eindeutig    schwer zu bestreiten
    verdaechtig  Anhaltspunkt, Auslegungsspielraum
    unklar       ein benoetigtes Signal wurde nicht erhoben
    unauffaellig nichts trifft zu

'unklar' bauen wir nicht — die Stufe entsteht von selbst, weil ein nicht
erhobenes Signal als MissingSignal ankommt. Wer nicht gemessen hat, kann
nichts behaupten.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .conditions import (Auswertung, MissingSignal, RuleSyntaxError,
                         Signaltabelle, auswerten)
from .rules import Bedingung, Regel
from .signale import ist_ableitung

EINDEUTIG = "eindeutig"
VERDAECHTIG = "verdaechtig"
UNKLAR = "unklar"
UNAUFFAELLIG = "unauffaellig"
NICHT_ANWENDBAR = "nicht_anwendbar"


@dataclass
class Befund:
    regel: Regel
    stufe: str
    bedingung: str | None = None
    begruendung: str | None = None
    nachweise: list = field(default_factory=list)   # je Signal: Wert, Schritt, Screenshot
    unklar_wegen: list = field(default_factory=list)
    herabgestuft: bool = False
    hinweise: list = field(default_factory=list)

    @property
    def berichtsrelevant(self) -> bool:
        """Was in die Beweisakte gehoert."""
        return self.stufe in (EINDEUTIG, VERDAECHTIG, UNKLAR)


def pruefe(regel: Regel, tabelle: Signaltabelle) -> Befund:
    anwendbar, unklar_anwendbarkeit, anwendbarkeitssignale = _anwendbar(regel, tabelle)

    if unklar_anwendbarkeit:
        return Befund(regel=regel, stufe=UNKLAR, unklar_wegen=unklar_anwendbarkeit,
                      hinweise=["Anwendbarkeit der Regel konnte nicht geprueft werden"])
    if not anwendbar:
        return Befund(regel=regel, stufe=NICHT_ANWENDBAR)

    # C4: Ist die Anwendbarkeit abgeleitet statt festgestellt, ist "eindeutig"
    # gesperrt. Bestaetigt ein Mensch die Voraussetzung im Zielprofil
    # (bestaetigt_durch_mensch), bleibt "eindeutig" moeglich.
    abgeleitet = [s for s in anwendbarkeitssignale
                  if ist_ableitung(s) and s not in tabelle.bestaetigt]

    unklar_wegen: list = []
    for stufe in (EINDEUTIG, VERDAECHTIG):
        for bedingung in regel.verdict_rules.get(stufe, []):
            treffer, fehlend = _bedingung(bedingung, tabelle)
            if fehlend:
                unklar_wegen.extend(fehlend)
                continue
            if treffer and treffer.wahr:
                return _treffer(regel, stufe, bedingung, treffer, tabelle,
                                abgeleitet, anwendbarkeitssignale)

    if unklar_wegen:
        return Befund(regel=regel, stufe=UNKLAR, unklar_wegen=_eindeutige(unklar_wegen))
    return Befund(regel=regel, stufe=UNAUFFAELLIG)


def _treffer(regel, stufe, bedingung, treffer, tabelle, abgeleitet, anwendbarkeitssignale):
    hinweise, herabgestuft = [], False

    if stufe == EINDEUTIG and abgeleitet:
        stufe = VERDAECHTIG
        herabgestuft = True
        hinweise.append(
            "Herabgestuft auf 'verdaechtig': die Anwendbarkeit stuetzt sich auf "
            "abgeleitete Signale (" + ", ".join(abgeleitet) + "), die niemand "
            "bestaetigt hat. Bestaetigung im Zielprofil unter "
            "'bestaetigt_durch_mensch' hebt die Begrenzung auf.")

    nachweise = [n for n in
                 (tabelle.nachweis(s) for s in
                  _eindeutige(list(treffer.benutzte_signale) + anwendbarkeitssignale))
                 if n]

    return Befund(regel=regel, stufe=stufe,
                  bedingung=" ".join(bedingung.text.split()),
                  begruendung=bedingung.begruendung, nachweise=nachweise,
                  herabgestuft=herabgestuft, hinweise=hinweise)


def _anwendbar(regel: Regel, tabelle: Signaltabelle):
    """(anwendbar, unklar_wegen, benutzte Signale)"""
    benutzte: list = []
    unklar: list = []

    def wahrheiten(bedingungen):
        ergebnisse = []
        for text in bedingungen:
            try:
                auswertung = auswerten(text, tabelle)
            except MissingSignal as fehler:
                unklar.append({"signal": fehler.name, "grund": fehler.grund})
                continue
            benutzte.extend(auswertung.benutzte_signale)
            ergebnisse.append(auswertung.wahr)
        return ergebnisse

    alle = wahrheiten(regel.applies_when.get("all", []))
    eines = wahrheiten(regel.applies_when.get("any", []))
    keines = wahrheiten(regel.applies_when.get("none", []))

    # Eine Regel, die ohnehin nicht greift, muss nicht "unklar" heissen:
    # steht schon fest, dass eine Voraussetzung fehlt, ist das eine Aussage.
    if (alle and not all(alle)) or (keines and any(keines)):
        return False, [], _eindeutige(benutzte)
    if unklar:
        return False, unklar, _eindeutige(benutzte)
    if regel.applies_when.get("any") and not any(eines):
        return False, [], _eindeutige(benutzte)
    return True, [], _eindeutige(benutzte)


def _bedingung(bedingung: Bedingung, tabelle: Signaltabelle):
    try:
        return auswerten(bedingung.text, tabelle), None
    except MissingSignal as fehler:
        return None, [{"signal": fehler.name, "grund": fehler.grund}]
    except RuleSyntaxError as fehler:
        return None, [{"signal": "(Regelwerksfehler)", "grund": str(fehler)}]


def _eindeutige(liste: list) -> list:
    gesehen, ergebnis = set(), []
    for eintrag in liste:
        schluessel = eintrag if isinstance(eintrag, str) else tuple(sorted(eintrag.items()))
        if schluessel not in gesehen:
            gesehen.add(schluessel)
            ergebnis.append(eintrag)
    return ergebnis
