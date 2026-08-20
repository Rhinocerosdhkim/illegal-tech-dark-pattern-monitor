"""Kann das System schweigen?

Die wichtigere Zahl ist nicht, wie viel wir finden, sondern wie oft wir
etwas behaupten, wo nichts ist. Ein System, das ueberall Verstoesse sieht,
ist fuer eine Verbraucherzentrale wertlos — und macht uns selbst angreifbar
(§ 4 Nr. 1, Nr. 2 UWG).

Beide Fixtures hier haben BEWUSST kein Zielprofil in data/targets/. Damit
wird zugleich geprueft, dass ein beliebiges, nicht von Hand eingerichtetes
Ziel durch die gesamte Kette laeuft.
"""

import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.lauf import lade_lauf
from dpm.engine.rules import lade_regelwerk
from dpm.engine.verdict import pruefe
from dpm.report.beweisakte import erzeuge

REGELN = lade_regelwerk()


def befunde(ordner):
    lauf = lade_lauf(ordner)
    return lauf, {b.regel.id: b for b in (pruefe(r, lauf.tabelle) for r in REGELN)}


print("Unauffaelliger Shop — kein Zielprofil, keine Handeinrichtung")
lauf, b = befunde("data/fixtures/sauberer-shop")
assert not lauf.tabelle.bestaetigt, "Fixture soll ohne Zielprofil laufen"
print("  ok  laeuft ohne data/targets/-Eintrag durch")

for regel_id in ("DP-001", "DP-002", "DP-003", "DP-004", "DP-005", "DP-006"):
    assert b[regel_id].stufe in ("unauffaellig", "unklar"), \
        f"{regel_id}: {b[regel_id].stufe} — Fehlalarm auf einer sauberen Seite"
print("  ok  kein einziger Befund auf der sauberen Seite")

assert b["DP-002"].stufe == "unauffaellig", \
    "'zahlungspflichtig bestellen' steht auf der Weissliste"
assert b["DP-003"].stufe == "unauffaellig", "kein Countdown, keine Knappheit"
assert b["DP-006"].stufe == "unauffaellig", "Pflichtinformation gut sichtbar"
print("  ok  DP-002, DP-003, DP-006 ausdruecklich unauffaellig")

print("\nRedaktionelles Portal — kein Shop, kein Banner")
lauf, b = befunde("data/fixtures/ratgeber-portal")
nicht_anwendbar = [i for i, x in b.items() if x.stufe == "nicht_anwendbar"]
assert len(nicht_anwendbar) >= 4, nicht_anwendbar
print(f"  ok  {len(nicht_anwendbar)} Regeln greifen gar nicht: {', '.join(sorted(nicht_anwendbar))}")

assert not any(x.berichtsrelevant and x.stufe != "unklar" for x in b.values()), \
    "Eine nicht anwendbare Regel darf nicht in der Beweisakte auftauchen"
print("  ok  nicht anwendbare Regeln stehen nicht in der Akte")

print("\nAlle vier Stufen sind damit mindestens einmal erzeugt worden")
gesehen = set()
for ordner in ("viagogo", "sauberer-shop", "ratgeber-portal"):
    _, x = befunde(f"data/fixtures/{ordner}")
    gesehen.update(v.stufe for v in x.values())
for stufe in ("eindeutig", "unklar", "unauffaellig", "nicht_anwendbar"):
    assert stufe in gesehen, f"{stufe} nie erzeugt"
    print(f"  ok  {stufe}")

print("\nBeweisakte laeuft auch fuer eine Seite ohne Befund")
with tempfile.TemporaryDirectory() as tmp:
    lauf, x = befunde("data/fixtures/ratgeber-portal")
    akte = erzeuge(lauf, list(x.values()), ausgabe=tmp, als_pdf=False)
    assert akte.html.exists()
    print(f"  ok  Akte erzeugt, {akte.anzahl_befunde} berichtsrelevante Eintraege")

print("\nAlle Tests bestanden.")
