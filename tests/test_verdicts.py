"""The fixture doubles as a regression test: if anyone changes the engine or
the rulebook such that a verdict moves, it shows up here.

A broken test here is not automatically a bug — but somebody has to look and
change the expected value deliberately.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.run import load_run
from dpm.engine.rules import load_rules
from dpm.engine.verdict import assess

run = load_run("data/fixtures/viagogo")
findings = {f.rule.id: f for f in (assess(r, run.table) for r in load_rules())}

EXPECTED = {
    # Beide Cookie-Bedingungen stehen seit dem 20.08. auf "verdaechtig":
    # § 25 Abs. 2 TDDDG nimmt technisch notwendige Speicherung aus, und ein
    # Zaehler kann sie nicht von Tracking unterscheiden (BEFUNDSTUFEN T2).
    # viagogo hat einen Ablehnen-Button, also greift der eine verbliebene
    # eindeutig-Zweig nicht.
    "DP-001": "verdaechtig",
    "DP-002": "verdaechtig",   # "Jetzt bestellen" is disputed, not clear-cut
    # PV hat den eindeutig-Zweig am 20.08. abgeraeumt: ein zuruecksetzender
    # Countdown belegt nur, dass der Zaehler sitzungsbezogen erzeugt wird -
    # nicht, dass die Angabe unwahr ist. Ersatz steht als Vorschlag in der
    # Datei und braucht countdown_unchanged_scans + countdown_personalized.
    # Bis dahin: die Knappheitsbedingung ist nicht auswertbar -> unklar.
    "DP-003": "unklar",
    # Die drei Tatsachensignale zum Dauerschuldverhaeltnis stehen jetzt auf
    # false: viagogo verkauft Tickets, kein Abonnement. Die Regel greift also
    # gar nicht - richtiger als das frueher Ausgewiesene "unklar".
    "DP-004": "nicht_anwendbar",
    # Neu seit dem 20.08.: fehlende MwSt-Angabe im Preisumfeld. Von der
    # Verbraucherzentrale im Seminar ausdruecklich genannt, bis dahin nutzte
    # keine Bedingung das Signal.
    "DP-005": "verdaechtig",
    "DP-006": "unklar",        # step "warenkorb" never reached
}

for rule_id, level in EXPECTED.items():
    got = findings[rule_id].level
    assert got == level, f"{rule_id}: {got}, expected {level}"
    print(f"  ok  {rule_id} -> {level}")

print("\nEvidence binding")
dp001 = findings["DP-001"]
assert dp001.evidence, "DP-001 without evidence"
for e in dp001.evidence:
    assert e["step"] and e["evidence"], f"evidence without provenance: {e}"
assert any(e["evidence"] == "S-01.png" for e in dp001.evidence)
print("  ok  every finding points at a step and a screenshot")

print("\nC4 — derivation vs. finding of fact")
assert not findings["DP-001"].downgraded, \
    "banner_detected is an observation, not a derivation — must not cap"
assert "is_b2c_offer" in run.table.confirmed, \
    "target profile no longer confirms is_b2c_offer"
print("  ok  facts do not cap, and neither do confirmed derivations")

print("\n'unklar' arises on its own")
gaps = {g["signal"]: g["reason"] for g in findings["DP-003"].unresolved}
assert "scarcity_value_unchanged_scans" in gaps, gaps
assert "Vergleichswert" in gaps["scarcity_value_unchanged_scans"]
print("  ok  measurement gap is passed through with its reason")

print("\n'unklar' can also be declared by the rule itself")
# DP-006 states in its own rulebook that a failed keyword search is not a
# finding but an open question (§ 5a Abs. 3 Nr. 2 UWG). On viagogo the
# signal is not even in signal_errors-free reach — the step "warenkorb" was
# never taken — so the automatic path fires instead. Both roads end at
# "unklar", which is the point; the declared form is exercised in
# tests/test_rule_defects.py.
dp006 = findings["DP-006"]
assert dp006.level == "unklar", dp006.level
assert any(g["signal"] == "required_info_found" and "warenkorb" in g["reason"]
           for g in dp006.unresolved), dp006.unresolved
print("  ok  a step that was never reached becomes unklar, with its reason")

print("\nAll verdict tests passed.")
