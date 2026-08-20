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
    "DP-001": "eindeutig",     # third-party cookies before any consent
    "DP-002": "eindeutig",     # label not on the whitelist
    "DP-003": "eindeutig",     # countdown resets on revisit
    "DP-004": "unklar",        # Dauerschuldverhaeltnis not measurable
    "DP-005": "unklar",        # checkout not reachable without login
    "DP-006": "unklar",        # step "warenkorb" never reached
}

for rule_id, level in EXPECTED.items():
    got = findings[rule_id].level
    assert got == level, f"{rule_id}: {got}, expected {level}"
    print(f"  ok  {rule_id} -> {level}")

print("\nEvidence binding")
dp003 = findings["DP-003"]
assert dp003.evidence, "DP-003 without evidence"
for e in dp003.evidence:
    assert e["step"] and e["evidence"], f"evidence without provenance: {e}"
assert any(e["evidence"] == "S-03.png" for e in dp003.evidence)
print("  ok  every finding points at a step and a screenshot")

print("\nC4 — derivation vs. finding of fact")
assert not findings["DP-001"].downgraded, \
    "banner_detected is an observation, not a derivation — must not cap"
assert "is_b2c_offer" in run.table.confirmed, \
    "target profile no longer confirms is_b2c_offer"
print("  ok  facts do not cap, and neither do confirmed derivations")

print("\n'unklar' arises on its own")
assert findings["DP-006"].unresolved[0]["signal"] == "required_info_found"
assert "warenkorb" in findings["DP-006"].unresolved[0]["reason"]
print("  ok  measurement gap is passed through with its reason")

print("\nAll verdict tests passed.")
