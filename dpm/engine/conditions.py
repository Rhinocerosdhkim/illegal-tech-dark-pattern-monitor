"""Bedingungsparser fuer rules/*.yaml — ohne eval().

Unterstuetzt genau das, was das Regelwerk tatsaechlich verwendet:

    Vergleich       a == b   a != b   a > b   a >= b   a < b   a <= b
    Verknuepfung    ... and ...
    Verhaeltnis     accept_button_area_px2 / reject_button_area_px2 > 2.0
    Listenpruefung  order_button_label not_in_whitelist ["a", "b"]
                    order_button_label in_greylist ["c", "d"]

Warum kein eval(): Eine Datei, die vom juristischen Team geschrieben wird,
darf niemals als Programmcode ausgefuehrt werden. Ausserdem waere ein
Tippfehler dann ein Absturz statt einer verstaendlichen Fehlermeldung.

Ein fehlendes Signal ist KEIN Fehler, sondern ein Befund: MissingSignal
wird nach oben gereicht und dort zur Stufe "unklar".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_VERGLEICH = re.compile(r"(>=|<=|==|!=|>|<)")
_LISTENOP = re.compile(r"\b(not_in_[a-z_]+|in_[a-z_]+)\b")
_ZAHL = re.compile(r"^-?\d+(\.\d+)?$")


class MissingSignal(Exception):
    """Ein benoetigtes Signal wurde nicht erhoben -> Befundstufe unklar."""

    def __init__(self, name: str, grund: str | None = None):
        self.name = name
        self.grund = grund
        super().__init__(f"Signal '{name}' nicht erhoben"
                         + (f": {grund}" if grund else ""))


class RuleSyntaxError(Exception):
    """Die Bedingung im Regelwerk ist nicht lesbar. Fehler des Regelwerks."""


@dataclass
class Signaltabelle:
    """Signalwerte eines Erfassungslaufs, plus Herkunftsnachweis.

    werte      Signalname -> {"wert", "schritt", "nachweis"}
    fehler     Signalname -> Begruendung, warum nicht gemessen werden konnte
    bestaetigt Signalnamen, die ein Mensch im Zielprofil bestaetigt hat (C4)
    """

    werte: dict
    fehler: dict = field(default_factory=dict)
    bestaetigt: set = field(default_factory=set)

    def hole(self, name: str):
        if name in self.werte:
            return self.werte[name]["wert"]
        if name in self.fehler:
            raise MissingSignal(name, self.fehler[name])
        raise MissingSignal(name, "nicht in der Erfassung enthalten")

    def nachweis(self, name: str) -> dict | None:
        eintrag = self.werte.get(name)
        if not eintrag:
            return None
        return {"signal": name,
                "wert": eintrag["wert"],
                "schritt": eintrag.get("schritt"),
                "nachweis": eintrag.get("nachweis")}


@dataclass
class Auswertung:
    wahr: bool
    benutzte_signale: list


def auswerten(bedingung: str, tabelle: Signaltabelle) -> Auswertung:
    """Wertet eine Bedingung aus. Kann MissingSignal werfen."""
    benutzt: list = []
    ergebnis = all(_teilbedingung(t, tabelle, benutzt)
                   for t in _trenne_und(_normalisiere(bedingung)))
    return Auswertung(wahr=ergebnis, benutzte_signale=benutzt)


# --- Zerlegung -----------------------------------------------------------

def _normalisiere(bedingung: str) -> str:
    """Vereinheitlicht die Schreibweisen, die in den Regeldateien vorkommen.

    DP-005 schreibt Bedingungen als YAML-Faltblock, wodurch der Wert mit
    Anfuehrungszeichen und Zeilenumbruechen ankommt. Das hier faengt das ab,
    damit das juristische Team seine Schreibweise nicht aendern muss.
    """
    text = " ".join(str(bedingung).split())
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1].strip()
    return text


def _trenne_und(text: str) -> list:
    """Trennt an ' and ', aber nicht innerhalb von [] oder Anfuehrungszeichen."""
    teile, puffer, tiefe, quote = [], [], 0, None
    worte = text.split(" ")
    for wort in worte:
        if wort == "and" and tiefe == 0 and quote is None:
            teile.append(" ".join(puffer))
            puffer = []
            continue
        if wort == "or" and tiefe == 0 and quote is None:
            raise RuleSyntaxError(
                "'or' wird nicht unterstuetzt. Fuer Oder-Verknuepfungen bitte "
                "mehrere Bedingungen unter derselben Befundstufe anlegen — "
                "die Stufe trifft, sobald eine davon zutrifft.")
        for zeichen in wort:
            if quote:
                if zeichen == quote:
                    quote = None
            elif zeichen in "\"'":
                quote = zeichen
            elif zeichen == "[":
                tiefe += 1
            elif zeichen == "]":
                tiefe -= 1
        puffer.append(wort)
    teile.append(" ".join(puffer))
    return [t.strip() for t in teile if t.strip()]


# --- Einzelbedingung -----------------------------------------------------

def _teilbedingung(text: str, tabelle: Signaltabelle, benutzt: list) -> bool:
    listenop = _LISTENOP.search(text)
    if listenop and "[" in text:
        return _listenpruefung(text, listenop, tabelle, benutzt)

    treffer = _VERGLEICH.search(text)
    if not treffer:
        raise RuleSyntaxError(f"Kein Vergleichsoperator in der Bedingung: {text!r}")

    links = text[:treffer.start()].strip()
    rechts = text[treffer.end():].strip()
    operator = treffer.group(1)

    a = _wert(links, tabelle, benutzt)
    b = _wert(rechts, tabelle, benutzt)

    if operator == "==":
        return a == b
    if operator == "!=":
        return a != b

    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)) \
            or isinstance(a, bool) or isinstance(b, bool):
        raise RuleSyntaxError(
            f"Operator '{operator}' braucht Zahlen, bekam {a!r} und {b!r} "
            f"in: {text!r}")

    return {">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[operator]


def _listenpruefung(text, listenop, tabelle: Signaltabelle, benutzt: list) -> bool:
    """'signal in_whitelist [...]' bzw. 'signal not_in_whitelist [...]'.

    Der Listenname (whitelist, greylist, ...) ist fuer die Auswertung
    bedeutungslos — er dokumentiert nur, wofuer die Liste juristisch steht.
    Verglichen wird ohne Ruecksicht auf Gross-/Kleinschreibung und
    ueberzaehlige Leerzeichen: § 312j BGB stellt auf den Wortlaut ab,
    nicht auf die Typografie.
    """
    signalname = text[:listenop.start()].strip()
    verneint = listenop.group(1).startswith("not_")

    beginn, ende = text.find("[", listenop.end()), text.rfind("]")
    if beginn == -1 or ende == -1:
        raise RuleSyntaxError(f"Liste nicht lesbar in: {text!r}")

    eintraege = [_entkleide(e) for e in
                 re.split(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)",
                          text[beginn + 1:ende]) if e.strip()]

    wert = _wert(signalname, tabelle, benutzt)
    enthalten = _falte(wert) in {_falte(e) for e in eintraege}
    return not enthalten if verneint else enthalten


def _falte(wert) -> str:
    return " ".join(str(wert).split()).casefold()


def _entkleide(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    return text.strip()


def _wert(zeichenkette: str, tabelle: Signaltabelle, benutzt: list):
    """Loest einen Operanden auf: Zahl, Wahrheitswert, Text oder Signal."""
    text = zeichenkette.strip()

    if "/" in text and not text[0] in "\"'":
        zaehler, _, nenner = text.partition("/")
        oben = _wert(zaehler, tabelle, benutzt)
        unten = _wert(nenner, tabelle, benutzt)
        if not isinstance(oben, (int, float)) or not isinstance(unten, (int, float)):
            raise RuleSyntaxError(f"Verhaeltnis braucht Zahlen: {text!r}")
        if unten == 0:
            # Division durch null ist keine Aussage, sondern eine Messluecke.
            raise MissingSignal(nenner.strip(), "Wert 0, Verhaeltnis nicht bildbar")
        return oben / unten

    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if _ZAHL.match(text):
        return float(text) if "." in text else int(text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]

    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", text):
        raise RuleSyntaxError(f"Kein gueltiger Signalname: {text!r}")

    if text not in benutzt:
        benutzt.append(text)
    return tabelle.hole(text)
