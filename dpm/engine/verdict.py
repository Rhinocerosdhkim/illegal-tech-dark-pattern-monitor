"""Vom Messwert zur Befundstufe.

    eindeutig       schwer zu bestreiten
    verdaechtig     Anhaltspunkt, Auslegungsspielraum
    unklar          ein benoetigtes Signal wurde nicht erhoben
    unauffaellig    nichts trifft zu
    nicht_anwendbar die Regel greift fuer diese Seite gar nicht

"unklar" bauen wir nicht — die Stufe entsteht von selbst, weil ein nicht
erhobenes Signal als MissingSignal ankommt.

Semantik bei fehlenden Signalen, nach DECISIONS.md vom 20.08. (A3 und
"Bedingungen werden einzeln ausgewertet"):

    Jede Bedingung wird EINZELN ausgewertet. Ist eine nicht auswertbar,
    wird nur sie uebersprungen und vermerkt; die uebrigen gelten weiter.
    Loest danach eine aus, steht der Befund. Loest keine aus und wurde
    mindestens eine uebersprungen, lautet er "unklar".

    Fuer die Anwendbarkeit gilt zusaetzlich: Wuerde die Regel ohnehin
    nicht anschlagen, wird sie stillschweigend uebersprungen. Andernfalls
    stuende in jedem Bericht zu jeder Seite ein "unklar" zu jeder Regel,
    und die Stufe verloere ihre Aussagekraft.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .conditions import (MissingSignal, RuleSyntaxError, Signaltabelle,
                         auswerten)
from .rules import Bedingung, Regel
from .signale import ist_ableitung

EINDEUTIG = "eindeutig"
VERDAECHTIG = "verdaechtig"
UNKLAR = "unklar"
UNAUFFAELLIG = "unauffaellig"
NICHT_ANWENDBAR = "nicht_anwendbar"

JA, NEIN, UNSICHER = "ja", "nein", "unsicher"


@dataclass
class Befund:
    regel: Regel
    stufe: str
    bedingung: str | None = None
    begruendung: str | None = None
    nachweise: list = field(default_factory=list)   # je Signal: Wert, Schritt, Screenshot
    unklar_wegen: list = field(default_factory=list)
    herabgestuft: bool = False
    wuerde_stufe: str | None = None                 # bei ungeklaerter Anwendbarkeit
    hinweise: list = field(default_factory=list)

    @property
    def berichtsrelevant(self) -> bool:
        """Was in die Beweisakte gehoert."""
        return self.stufe in (EINDEUTIG, VERDAECHTIG, UNKLAR)


def pruefe(regel: Regel, tabelle: Signaltabelle) -> Befund:
    zustand, offen, aw_signale = _anwendbar(regel, tabelle)

    if zustand == NEIN:
        return Befund(regel=regel, stufe=NICHT_ANWENDBAR)

    # C4: Ist die Anwendbarkeit abgeleitet statt festgestellt, ist "eindeutig"
    # gesperrt. Bestaetigt ein Mensch die Voraussetzung im Zielprofil
    # (bestaetigt_durch_mensch), bleibt "eindeutig" moeglich.
    abgeleitet = [s for s in aw_signale
                  if ist_ableitung(s) and s not in tabelle.bestaetigt]

    uebersprungen: list = []
    for stufe in (EINDEUTIG, VERDAECHTIG):
        for bedingung in regel.verdict_rules.get(stufe, []):
            treffer, luecken = _bedingung(bedingung, regel, tabelle)
            if luecken:
                uebersprungen.extend(luecken)
                continue
            if treffer and treffer.wahr:
                if zustand == UNSICHER:
                    return _anwendbarkeit_offen(regel, stufe, bedingung, offen)
                return _treffer(regel, stufe, bedingung, treffer, tabelle,
                                abgeleitet, aw_signale)

    if uebersprungen:
        return Befund(regel=regel, stufe=UNKLAR, unklar_wegen=_eindeutige(uebersprungen))
    if zustand == UNSICHER:
        # Die Regel wuerde ohnehin nicht anschlagen — stillschweigend uebergehen,
        # statt die Akte mit einem nichtssagenden "unklar" zu fuellen.
        return Befund(regel=regel, stufe=NICHT_ANWENDBAR)
    return Befund(regel=regel, stufe=UNAUFFAELLIG)


def _anwendbarkeit_offen(regel, stufe, bedingung, offen) -> Befund:
    return Befund(
        regel=regel, stufe=UNKLAR, wuerde_stufe=stufe,
        bedingung=" ".join(bedingung.text.split()),
        unklar_wegen=offen,
        hinweise=[f"Die Regel wuerde anschlagen ({stufe}); ob sie auf diese "
                  f"Seite ueberhaupt anwendbar ist, konnte nicht geprueft "
                  f"werden."])


def _treffer(regel, stufe, bedingung, treffer, tabelle, abgeleitet, aw_signale):
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
                  _eindeutige(list(treffer.benutzte_signale) + aw_signale))
                 if n]

    return Befund(regel=regel, stufe=stufe,
                  bedingung=" ".join(bedingung.text.split()),
                  begruendung=bedingung.begruendung, nachweise=nachweise,
                  herabgestuft=herabgestuft, hinweise=hinweise)


def _anwendbar(regel: Regel, tabelle: Signaltabelle):
    """(ja | nein | unsicher, uebersprungene Bedingungen, benutzte Signale)"""
    benutzte: list = []
    offen: list = []

    def wahrheiten(bedingungen):
        ergebnisse = []
        for text in bedingungen:
            auswertung, luecken = _bedingung(Bedingung(text=text), regel, tabelle)
            if luecken:
                offen.extend(luecken)
                continue
            benutzte.extend(auswertung.benutzte_signale)
            ergebnisse.append(auswertung.wahr)
        return ergebnisse

    alle = wahrheiten(regel.applies_when.get("all", []))
    eines = wahrheiten(regel.applies_when.get("any", []))
    keines = wahrheiten(regel.applies_when.get("none", []))
    hat_any = bool(regel.applies_when.get("any"))

    # Steht schon fest, dass eine Voraussetzung fehlt, ist das eine Aussage —
    # kein "unklar".
    if any(w is False for w in alle) or any(w is True for w in keines):
        return NEIN, [], _eindeutige(benutzte)
    if hat_any and any(eines):
        pass                                  # mindestens eines erfuellt
    elif hat_any and not offen:
        return NEIN, [], _eindeutige(benutzte)

    if offen:
        return UNSICHER, _eindeutige(offen), _eindeutige(benutzte)
    return JA, [], _eindeutige(benutzte)


def _bedingung(bedingung: Bedingung, regel: Regel, tabelle: Signaltabelle):
    try:
        return auswerten(bedingung.text, tabelle, regel.listen), None
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
