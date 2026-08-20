"""Ein Einstiegspunkt, ein Ausgabeordner, keine Einrichtung.

    python -m dpm befund data/fixtures/viagogo

Entwurfsvorgabe aus AGENDA_Technik.md §6: Am Montag muss eine Person ohne
Entwicklungshintergrund das hier allein bedienen koennen.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from dpm.report.beweisakte import erzeuge as erzeuge_akte
from dpm.engine.lauf import lade_lauf
from dpm.engine.rules import lade_regelwerk
from dpm.engine.verdict import (EINDEUTIG, NICHT_ANWENDBAR, UNAUFFAELLIG,
                                UNKLAR, VERDAECHTIG, pruefe)

ANZEIGE = {EINDEUTIG: "eindeutig", VERDAECHTIG: "verdaechtig",
           UNKLAR: "unklar", UNAUFFAELLIG: "unauffaellig",
           NICHT_ANWENDBAR: "nicht anwendbar"}


def befund(argumente) -> int:
    lauf = lade_lauf(argumente.lauf)
    regeln = lade_regelwerk(argumente.regeln)
    befunde = [pruefe(regel, lauf.tabelle) for regel in regeln]

    print(f"\nZiel      {lauf.meta.get('ziel')}  ({lauf.branche})")
    print(f"Erfassung {lauf.meta.get('timestamp')}   {lauf.run_id}")
    print(f"Signale   {len(lauf.tabelle.werte)} gemessen, "
          f"{len(lauf.tabelle.fehler)} nicht erhoben")
    _warnungen(lauf)
    print()

    kopf = f"{'Regel':8} {'Kategorie':13} {'Stufe':15} {'Status':8} Muster"
    print(kopf)
    print("-" * len(kopf))
    for b in befunde:
        print(f"{b.regel.id:8} {b.regel.kategorie:13} "
              f"{ANZEIGE[b.stufe]:15} {b.regel.status:8} {b.regel.name_de[:44]}")

    for b in befunde:
        if not b.berichtsrelevant:
            continue
        print(f"\n── {b.regel.id} · {ANZEIGE[b.stufe].upper()} "
              f"{'(herabgestuft)' if b.herabgestuft else ''}")
        print(f"   Norm       {b.regel.norm}")
        if b.bedingung:
            print(f"   Bedingung  {b.bedingung}")
        for nachweis in b.nachweise:
            print(f"   Nachweis   {nachweis['signal']} = {nachweis['wert']!r}"
                  f"   [{nachweis['schritt']} · {nachweis['nachweis']}]")
        for luecke in b.unklar_wegen:
            print(f"   Nicht erhoben  {luecke['signal']} — {luecke['grund']}")
        for hinweis in b.hinweise:
            print(f"   Hinweis    {hinweis}")

    zaehlung = {stufe: sum(1 for b in befunde if b.stufe == stufe) for stufe in ANZEIGE}
    print("\n" + "  ".join(f"{ANZEIGE[s]}: {n}" for s, n in zaehlung.items() if n))
    print()
    return 0


def akte(argumente) -> int:
    lauf = lade_lauf(argumente.lauf)
    befunde = [pruefe(regel, lauf.tabelle)
               for regel in lade_regelwerk(argumente.regeln)]

    ergebnis = erzeuge_akte(lauf, befunde, ausgabe=argumente.ausgabe,
                            als_pdf=not argumente.nur_html)

    print()
    _warnungen(lauf)
    print(f"\nBeweisakte {lauf.meta.get('ziel')} — "
          f"{ergebnis.anzahl_befunde} Befunde")
    print(f"  {ergebnis.html}")
    if ergebnis.pdf:
        groesse = ergebnis.pdf.stat().st_size // 1024
        print(f"  {ergebnis.pdf}  ({groesse} kB)")
    else:
        print("  (kein PDF — Playwright nicht verfuegbar)")
    print()
    return 0


def _warnungen(lauf) -> None:
    for warnung in lauf.warnungen:
        print(f"  ! {warnung}")


def main(argv=None) -> int:
    zerleger = argparse.ArgumentParser(prog="dpm", description=__doc__)
    unterbefehle = zerleger.add_subparsers(dest="befehl", required=True)

    b = unterbefehle.add_parser("befund", help="Erfassungslauf gegen das Regelwerk pruefen")
    b.add_argument("lauf", type=Path, help="Ordner mit capture.json")
    b.add_argument("--regeln", type=Path, default=None)
    b.set_defaults(funktion=befund)

    a = unterbefehle.add_parser("akte", help="Beweisakte als HTML und PDF erzeugen")
    a.add_argument("lauf", type=Path, help="Ordner mit capture.json")
    a.add_argument("--regeln", type=Path, default=None)
    a.add_argument("--ausgabe", type=Path, default=Path("out"))
    a.add_argument("--nur-html", action="store_true", dest="nur_html",
                   help="ohne PDF, fuer schnelles Ausprobieren")
    a.set_defaults(funktion=akte)

    argumente = zerleger.parse_args(argv)

    # Fehlermeldungen muessen fuer eine Person handhabbar sein, die nicht
    # entwickelt: ab Dienstag steht niemand aus der Entwicklung bereit.
    try:
        return argumente.funktion(argumente)
    except FileNotFoundError as fehler:
        print(f"\nDatei nicht gefunden: {fehler}\n"
              f"Erwartet wird ein Ordner mit einer capture.json darin.\n",
              file=sys.stderr)
    except json.JSONDecodeError as fehler:
        print(f"\nDie capture.json ist nicht lesbar (Zeile {fehler.lineno}): "
              f"{fehler.msg}\n", file=sys.stderr)
    except yaml.YAMLError as fehler:
        print(f"\nEine YAML-Datei ist nicht lesbar:\n{fehler}\n", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
