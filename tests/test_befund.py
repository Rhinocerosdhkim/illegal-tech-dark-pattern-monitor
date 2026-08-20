"""Die Fixture ist zugleich Regressionstest: Aendert jemand Engine oder
Regelwerk so, dass sich ein Befund verschiebt, faellt das hier auf.

Wenn ein Test hier bricht, ist das nicht automatisch ein Fehler — aber es
muss jemand hinsehen und den erwarteten Wert bewusst aendern.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.lauf import lade_lauf
from dpm.engine.rules import lade_regelwerk
from dpm.engine.verdict import pruefe

lauf = lade_lauf("data/fixtures/viagogo")
befunde = {b.regel.id: b for b in
           (pruefe(r, lauf.tabelle) for r in lade_regelwerk())}

ERWARTET = {
    "DP-001": "eindeutig",     # Drittanbieter-Cookies vor jeder Einwilligung
    "DP-002": "eindeutig",     # Beschriftung nicht auf der Weissliste
    "DP-003": "eindeutig",     # Countdown springt beim Wiederaufruf zurueck
    "DP-004": "unklar",        # Dauerschuldverhaeltnis nicht messbar
    "DP-005": "unklar",        # Kasse ohne Anmeldung nicht erreichbar
    "DP-006": "unklar",        # Schritt warenkorb nicht erreicht
}

for regel_id, stufe in ERWARTET.items():
    ist = befunde[regel_id].stufe
    assert ist == stufe, f"{regel_id}: {ist}, erwartet {stufe}"
    print(f"  ok  {regel_id} -> {stufe}")

print("\nBeweisbindung")
dp003 = befunde["DP-003"]
assert dp003.nachweise, "DP-003 ohne Nachweis"
for n in dp003.nachweise:
    assert n["schritt"] and n["nachweis"], f"Nachweis ohne Herkunft: {n}"
assert any(n["nachweis"] == "S-03.png" for n in dp003.nachweise)
print("  ok  jeder Befund zeigt auf Schritt und Screenshot")

print("\nC4 — Ableitung gegen Feststellung")
assert not befunde["DP-001"].herabgestuft, \
    "banner_detected ist eine Beobachtung, keine Ableitung — darf nicht begrenzen"
assert "is_b2c_offer" in lauf.tabelle.bestaetigt, \
    "Zielprofil bestaetigt is_b2c_offer nicht mehr"
print("  ok  Feststellungen begrenzen nicht, bestaetigte Ableitungen auch nicht")

print("\nunklar entsteht von selbst")
assert befunde["DP-006"].unklar_wegen[0]["signal"] == "required_info_found"
assert "warenkorb" in befunde["DP-006"].unklar_wegen[0]["grund"]
print("  ok  Messluecke wird mit Begruendung durchgereicht")

print("\nAlle Befundtests bestanden.")
