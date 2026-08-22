"""The accuracy figure — and the three ways it could quietly lie.

The false-alarm rate is the number the consumer agency asks for. It is
also the easiest one to compute in a way that flatters us, so the checks
here are about the denominators, not about the code running at all.
"""

import sys
import pathlib
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.discovery import find_runs
from dpm.engine.rules import load_rules
from dpm.engine.run import load_run
from dpm.engine.verdict import NOT_APPLICABLE, NO_FINDING, UNRESOLVED
from dpm.report.gold import compare, domain, rate, read
from dpm.report.overview import collect

HEADER = ("url,branche,pattern_id,kategorie,befund_mensch,nachweis,"
          "bearbeiter,datum,notiz\n")

print("Sites are matched by host, not by spelling")
for written, expected in [("https://www.viagogo.de/Event/1", "viagogo.de"),
                          ("viagogo.de", "viagogo.de"),
                          ("HTTP://VIAGOGO.DE/", "viagogo.de"),
                          ("", "")]:
    assert domain(written) == expected, written
print("  ok  scheme, www and path ignored")

paths = find_runs("data/fixtures")
rules = load_rules()
overview = collect(paths, rules)

print("\nA hand-written fixture is never compared against a human verdict")
# It carries the verdicts we wanted to see, so holding it against a person
# measures our own consistency and nothing else. Worse, viagogo-2026-09 is
# dated in the future and would win every "most recent capture" match.
real_fixtures = [load_run(p) for p in paths]
rows = [{"url": "https://www.viagogo.de", "pattern_id": "DP-003",
         "befund_mensch": "unauffaellig", "notiz": ""}]
result = compare(rows, overview.rows, real_fixtures)
assert not result.rows, f"a fixture was used as a measurement: {result.rows}"
assert len(result.uncovered) == 1, result
assert result.fixtures_ignored == len(real_fixtures), result.fixtures_ignored
print(f"  ok  {result.fixtures_ignored} Fixtures uebergangen, Zeile als "
      f"'ohne Erfassung' gemeldet")

# The rest of this file is about the matching and the denominators, which
# need captures to match against. The fixtures stand in for real ones.
runs = []
for path in paths:
    run = load_run(path)
    run.meta["capture_mode"] = "headless"
    runs.append(run)

print("\nA site captured twice is compared against the newer capture")
rows = [{"url": "https://www.viagogo.de", "pattern_id": "DP-003",
         "befund_mensch": "unauffaellig", "notiz": ""}]
result = compare(rows, overview.rows, runs)
assert len(result.rows) == 1, result
assert "2026-09" in result.rows[0]["run_id"], result.rows[0]
print(f"  ok  compared against {result.rows[0]['run_id']}")

print("\nA gold row without a capture is reported, not dropped")
rows = [{"url": "https://nie-erfasst.de", "pattern_id": "DP-001",
         "befund_mensch": "eindeutig", "notiz": ""}]
result = compare(rows, overview.rows, runs)
assert not result.rows and len(result.uncovered) == 1, result
print("  ok  counted as uncovered")

print("\nA row we cannot read is not silently ignored")
rows = [{"url": "", "pattern_id": "", "befund_mensch": "", "notiz": ""},
        {"url": "https://www.viagogo.de", "pattern_id": "DP-001",
         "befund_mensch": "vielleicht", "notiz": ""}]
result = compare(rows, overview.rows, runs)
assert len(result.unreadable) == 2, result
print("  ok  both bad rows reported as unreadable")

print("\n'unklar' is neither a hit nor a mistake")
# DP-006 on viagogo is unklar in the fixture — see tests/test_verdicts.py.
rows = [{"url": "https://www.viagogo.de", "pattern_id": "DP-006",
         "befund_mensch": "eindeutig", "notiz": ""}]
result = compare(rows, overview.rows, runs)
assert len(result.rows) == 1
assert result.rows[0]["system"] == UNRESOLVED, result.rows[0]
assert result.unresolved and not result.decided, result
assert not result.missed, "an unmeasurable signal was counted as a miss"
assert not result.false_alarms
print("  ok  excluded from every rate instead of counted as wrong")

print("\nThe false-alarm rate is taken over the clean rows only")
# sauberer-shop is the deliberately unremarkable fixture.
rows = [{"url": "https://www.beispielshop.de", "pattern_id": "DP-002",
         "befund_mensch": "unauffaellig", "notiz": ""},
        {"url": "https://www.viagogo.de", "pattern_id": "DP-001",
         "befund_mensch": "verdaechtig", "notiz": ""}]
result = compare(rows, overview.rows, runs)
clean = [r for r in result.decided if r["human"] == NO_FINDING]
assert len(clean) == 1, f"the clean row was not decided: {result.rows}"
assert all(r["human"] == NO_FINDING for r in result.clean), result.clean
assert len(result.clean) == len(clean)
# Adding guilty sites must not improve the false-alarm rate.
before = rate(result.false_alarms, result.clean)
more = rows + [{"url": "https://www.viagogo.de", "pattern_id": "DP-002",
                "befund_mensch": "verdaechtig", "notiz": ""}]
after = compare(more, overview.rows, runs)
assert rate(after.false_alarms, after.clean) == before, \
    "the false-alarm rate moved when only guilty rows were added"
print(f"  ok  unchanged at {before} when guilty rows are added")

print("\n'nicht anwendbar' counts as a miss when the human found something")
# The system asserts that the rule does not apply here. If a person found a
# violation of exactly that rule, we were silent about it. Counting only
# "unauffaellig" made the miss rate better the more often a rule excluded
# itself — ratgeber-portal answers nicht_anwendbar for all six.
rows = [{"url": "https://www.beispiel-ratgeber.de", "pattern_id": "DP-001",
         "befund_mensch": "eindeutig", "notiz": ""}]
result = compare(rows, overview.rows, runs)
assert len(result.rows) == 1, result
assert result.rows[0]["system"] == NOT_APPLICABLE, result.rows[0]
assert result.missed, "a rule that excluded itself was not counted as a miss"
print(f"  ok  gezaehlt als uebersehen, nicht als Enthaltung")

print("\nA rule that excluded itself is out of the false-alarm denominator")
# A rule that does not apply cannot raise a false alarm, so counting it in
# the denominator improves the rate for free: point DP-004 at enough shops
# without a subscription and the figure approaches zero without the system
# getting any better.
rows = [{"url": "https://www.beispiel-ratgeber.de", "pattern_id": "DP-002",
         "befund_mensch": "unauffaellig", "notiz": ""},
        {"url": "https://www.beispielshop.de", "pattern_id": "DP-002",
         "befund_mensch": "unauffaellig", "notiz": ""}]
result = compare(rows, overview.rows, runs)
assert len(result.rows) == 2, result
systeme = sorted(r["system"] for r in result.rows)
assert NOT_APPLICABLE in systeme, systeme
assert all(r["system"] != NOT_APPLICABLE for r in result.clean), \
    "a rule that excluded itself padded the false-alarm denominator"
print(f"  ok  {len(result.clean)} von {len(result.rows)} Zeilen im Nenner")

print("\nAn empty gold standard yields no figure at all")
with tempfile.TemporaryDirectory() as tmp:
    empty = pathlib.Path(tmp) / "gold.csv"
    empty.write_text(HEADER, encoding="utf-8")
    assert read(empty) == [], "a header-only file must not count as data"
print("  ok  header-only file reports nothing rather than 0 %")

print("\nAll gold-standard tests passed.")
