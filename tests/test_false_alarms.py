"""Can the system stay silent?

The more important number is not how much we find, but how often we assert
something where there is nothing. A system that sees violations everywhere
is worthless to a consumer protection agency — and makes us attackable
ourselves (§ 4 nos. 1 and 2 UWG).

Both fixtures here deliberately have no target profile in data/targets/.
That also verifies that an arbitrary target nobody set up by hand runs
through the entire chain.
"""

import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.run import load_run
from dpm.engine.rules import load_rules
from dpm.engine.verdict import assess
from dpm.report.case_file import build

RULES = load_rules()


def findings_for(folder):
    run = load_run(folder)
    return run, {f.rule.id: f for f in (assess(r, run.table) for r in RULES)}


print("Unremarkable shop — no target profile, no hand setup")
run, f = findings_for("data/fixtures/sauberer-shop")
assert not run.table.confirmed, "fixture is meant to run without a profile"
print("  ok  runs without an entry in data/targets/")

for rule_id in ("DP-001", "DP-002", "DP-003", "DP-004", "DP-005", "DP-006"):
    assert f[rule_id].level in ("unauffaellig", "unklar"), \
        f"{rule_id}: {f[rule_id].level} — false alarm on a clean site"
print("  ok  not a single finding on the clean site")

assert f["DP-002"].level == "unauffaellig", \
    "'zahlungspflichtig bestellen' is on the whitelist"
assert f["DP-003"].level == "unauffaellig", "no countdown, no scarcity"
assert f["DP-006"].level == "unauffaellig", "mandatory information clearly visible"
print("  ok  DP-002, DP-003, DP-006 explicitly unremarkable")

print("\nEditorial portal — no shop, no banner")
run, f = findings_for("data/fixtures/ratgeber-portal")
not_applicable = [i for i, x in f.items() if x.level == "nicht_anwendbar"]
assert len(not_applicable) >= 4, not_applicable
print(f"  ok  {len(not_applicable)} rules do not apply: {', '.join(sorted(not_applicable))}")

assert not any(x.reportable and x.level != "unklar" for x in f.values()), \
    "a non-applicable rule must not appear in the Beweisakte"
print("  ok  non-applicable rules stay out of the file")

print("\nAll four levels have now been produced at least once")
seen = set()
for folder in ("viagogo", "sauberer-shop", "ratgeber-portal"):
    _, x = findings_for(f"data/fixtures/{folder}")
    seen.update(v.level for v in x.values())
for level in ("eindeutig", "unklar", "unauffaellig", "nicht_anwendbar"):
    assert level in seen, f"{level} never produced"
    print(f"  ok  {level}")

print("\nThe Beweisakte also builds for a site without any finding")
with tempfile.TemporaryDirectory() as tmp:
    run, x = findings_for("data/fixtures/ratgeber-portal")
    case = build(run, list(x.values()), output=tmp, as_pdf=False)
    assert case.html.exists()
    print(f"  ok  file built, {case.finding_count} reportable entries")

print("\nAll false-alarm tests passed.")
