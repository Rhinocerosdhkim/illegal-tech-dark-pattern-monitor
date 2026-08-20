"""Bedingungsparser fuer rules/*.yaml — ohne eval().

Unterstuetzt genau das, was rules/_VORLAGE.yaml dem juristischen Team zusagt:

    Vergleich       == != > >= < <=
    Verknuepfung    and   or          (and bindet staerker)
    Rechnung        accept_button_area_px2 / reject_button_area_px2 > 2.0
                    accept_contrast_ratio - reject_contrast_ratio > 3.0
    Listen          kuendigungsbutton_label not in zulaessige_labels
                    order_button_label not_in_whitelist ["a", "b"]

Warum kein eval(): Eine Datei, die vom juristischen Team geschrieben wird,
darf niemals als Programmcode ausgefuehrt werden. Ausserdem waere ein
Tippfehler dann ein Absturz statt einer verstaendlichen Fehlermeldung.

Dreiwertige Logik. Ein fehlendes Signal macht eine Bedingung nicht
automatisch unauswertbar:

    a and b   ist falsch, sobald ein Glied falsch ist — auch wenn ein
              anderes nicht gemessen wurde
    a or b    ist wahr, sobald ein Glied wahr ist — ebenso

Erst wenn das Ergebnis wirklich von dem fehlenden Wert abhaengt, wird
MissingSignal geworfen und daraus oben die Stufe "unklar". Das ist nicht
Bequemlichkeit, sondern Genauigkeit: Wir sollen nur dort "unklar" sagen,
wo wir es tatsaechlich nicht wissen.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_VERGLEICH = re.compile(r"(>=|<=|==|!=|>|<)")
_LISTENOP_INLINE = re.compile(r"\b(not_in_[a-z_]+|in_[a-z_]+)\b")
_LISTENOP_BENANNT = re.compile(
    r"^([a-zA-Z_][a-zA-Z0-9_]*)\s+(not\s+in|in)\s+([a-zA-Z_][a-zA-Z0-9_]*)$")
_ZAHL = re.compile(r"^-?\d+(\.\d+)?$")
_NAME = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Rechenzeichen nur mit Leerzeichen ringsum. Sonst waere "-1" nicht mehr von
# einer Subtraktion zu unterscheiden.
_RECHNEN = {"/": lambda a, b: a / b, "-": lambda a, b: a - b,
            "+": lambda a, b: a + b, "*": lambda a, b: a * b}


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


def auswerten(bedingung: str, tabelle: Signaltabelle,
              listen: dict | None = None) -> Auswertung:
    """Wertet eine Bedingung aus. Kann MissingSignal oder RuleSyntaxError werfen."""
    benutzt: list = []
    wahr = _oder(_normalisiere(bedingung), tabelle, listen or {}, benutzt)
    return Auswertung(wahr=wahr, benutzte_signale=benutzt)


# --- Verknuepfung, dreiwertig -------------------------------------------

def _oder(text: str, tabelle, listen, benutzt) -> bool:
    werte, fehlend = _glieder(_trenne(text, "or"),
                              lambda t: _und(t, tabelle, listen, benutzt))
    if any(werte):
        return True
    if fehlend:
        raise fehlend[0]
    return False


def _und(text: str, tabelle, listen, benutzt) -> bool:
    werte, fehlend = _glieder(_trenne(text, "and"),
                              lambda t: _teilbedingung(t, tabelle, listen, benutzt))
    if not all(werte):
        return False
    if fehlend:
        raise fehlend[0]
    return True


def _glieder(teile: list, auswerter):
    werte, fehlend = [], []
    for teil in teile:
        try:
            werte.append(auswerter(teil))
        except MissingSignal as fehler:
            fehlend.append(fehler)
    return werte, fehlend


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


def _trenne(text: str, schluesselwort: str) -> list:
    """Trennt an ' and ' bzw. ' or ', aber nicht in [] oder Anfuehrungszeichen."""
    teile, puffer, tiefe, quote = [], [], 0, None
    for wort in text.split(" "):
        if wort == schluesselwort and tiefe == 0 and quote is None:
            teile.append(" ".join(puffer))
            puffer = []
            continue
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

def _teilbedingung(text: str, tabelle, listen, benutzt) -> bool:
    benannt = _LISTENOP_BENANNT.match(text)
    if benannt:
        return _liste(benannt.group(1), benannt.group(3),
                      benannt.group(2).startswith("not"),
                      _aus_listen(benannt.group(3), listen, text),
                      tabelle, benutzt)

    inline = _LISTENOP_INLINE.search(text)
    if inline and "[" in text:
        return _liste(text[:inline.start()].strip(), None,
                      inline.group(1).startswith("not_"),
                      _inline_liste(text, inline), tabelle, benutzt)

    treffer = _VERGLEICH.search(text)
    if not treffer:
        raise RuleSyntaxError(f"Kein Vergleichsoperator in der Bedingung: {text!r}")

    operator = treffer.group(1)
    a = _wert(text[:treffer.start()], tabelle, listen, benutzt)
    b = _wert(text[treffer.end():], tabelle, listen, benutzt)

    if operator == "==":
        return a == b
    if operator == "!=":
        return a != b

    for wert in (a, b):
        if not isinstance(wert, (int, float)) or isinstance(wert, bool):
            raise RuleSyntaxError(
                f"Operator '{operator}' braucht Zahlen, bekam {a!r} und {b!r} "
                f"in: {text!r}")
    return {">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[operator]


def _aus_listen(name: str, listen: dict, text: str) -> list:
    if name not in (listen or {}):
        raise RuleSyntaxError(
            f"Die Regel verweist auf die Liste '{name}', die unter 'listen:' "
            f"nicht angelegt ist. Bedingung: {text!r}")
    return [str(e) for e in listen[name]]


def _inline_liste(text: str, inline) -> list:
    beginn, ende = text.find("[", inline.end()), text.rfind("]")
    if beginn == -1 or ende == -1:
        raise RuleSyntaxError(f"Liste nicht lesbar in: {text!r}")
    return [_entkleide(e) for e in
            re.split(r",(?=(?:[^\"']*[\"'][^\"']*[\"'])*[^\"']*$)",
                     text[beginn + 1:ende]) if e.strip()]


def _liste(signalname: str, listenname, verneint: bool, eintraege: list,
           tabelle, benutzt) -> bool:
    """Zugehoerigkeit zu einer Wortliste.

    Verglichen wird ohne Ruecksicht auf Gross-/Kleinschreibung und
    ueberzaehlige Leerzeichen: § 312j BGB stellt auf den Wortlaut ab,
    nicht auf die Typografie. Welche Liste (Weiss-, Grau-, Positivliste)
    gemeint ist, hat fuer die Auswertung keine Bedeutung — der Name
    dokumentiert nur, wofuer sie juristisch steht.
    """
    wert = _wert(signalname, tabelle, {}, benutzt)
    enthalten = _falte(wert) in {_falte(e) for e in eintraege}
    return not enthalten if verneint else enthalten


def _falte(wert) -> str:
    return " ".join(str(wert).split()).casefold()


def _entkleide(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        text = text[1:-1]
    return text.strip()


def _wert(zeichenkette: str, tabelle, listen, benutzt):
    """Loest einen Operanden auf: Rechnung, Zahl, Wahrheitswert, Text, Signal."""
    text = zeichenkette.strip()

    teile = text.split(" ")
    if len(teile) == 3 and teile[1] in _RECHNEN:
        links = _wert(teile[0], tabelle, listen, benutzt)
        rechts = _wert(teile[2], tabelle, listen, benutzt)
        for wert in (links, rechts):
            if not isinstance(wert, (int, float)) or isinstance(wert, bool):
                raise RuleSyntaxError(f"Rechnung braucht Zahlen: {text!r}")
        if teile[1] == "/" and rechts == 0:
            # Division durch null ist keine Aussage, sondern eine Messluecke.
            raise MissingSignal(teile[2], "Wert 0, Verhaeltnis nicht bildbar")
        return _RECHNEN[teile[1]](links, rechts)

    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if _ZAHL.match(text):
        return float(text) if "." in text else int(text)
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]

    if not _NAME.match(text):
        raise RuleSyntaxError(f"Kein gueltiger Signalname: {text!r}")

    if text not in benutzt:
        benutzt.append(text)
    return tabelle.hole(text)
