"""Ein Einstiegspunkt, ein Ausgabeordner, keine Einrichtung.

    python -m dpm befund data/fixtures/viagogo

Entwurfsvorgabe aus AGENDA_Technik.md §6: Am Montag muss eine Person ohne
Entwicklungshintergrund das hier allein bedienen koennen.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
          f"{len(lauf.tabelle.fehler)} nicht erhoben\n")

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


def main(argv=None) -> int:
    zerleger = argparse.ArgumentParser(prog="dpm", description=__doc__)
    unterbefehle = zerleger.add_subparsers(dest="befehl", required=True)

    b = unterbefehle.add_parser("befund", help="Erfassungslauf gegen das Regelwerk pruefen")
    b.add_argument("lauf", type=Path, help="Ordner mit capture.json")
    b.add_argument("--regeln", type=Path, default=Path("rules"))
    b.set_defaults(funktion=befund)

    argumente = zerleger.parse_args(argv)
    return argumente.funktion(argumente)


if __name__ == "__main__":
    sys.exit(main())
