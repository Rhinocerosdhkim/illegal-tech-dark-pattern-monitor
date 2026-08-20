"""The Zeitachse is the third of the three arguments the presentation rests
on, and the one that connects to enforcement: a company that gave a
cease-and-desist undertaking and quietly reintroduces the design.

The case that matters most here is the one a naive diff misses — the verdict
level stays the same while the facts underneath change completely.
"""

import json, sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.rules import load_rules
from dpm.report.diff import (NEW, RESOLVED, SAME_LEVEL_NEW_REASON, UNCHANGED,
                             build, compare)

RULES = load_rules()
EARLIER, LATER = "data/fixtures/viagogo", "data/fixtures/viagogo-2026-09"

timeline = compare(EARLIER, LATER, RULES)
changes = {c.rule_id: c for c in timeline.rule_changes}

print("Three weeks later on the same site")
assert not timeline.warnings, timeline.warnings
print("  ok  same target, correct order, same viewport — no objections")

print("\nA finding disappears")
c = changes["DP-002"]
assert (c.kind, c.before_level, c.after_level) == (RESOLVED, "verdaechtig", "unauffaellig"), c
assert c.before_condition and not c.after_condition
print("  ok  DP-002 verdaechtig -> unauffaellig, earlier condition recorded")

# DP-003 no longer carries a finding at all (PV removed the eindeutig branch),
# so the countdown disappearing now shows up as a change in what could be
# measured, not as a finding that was resolved. That is the honest reading.
c = changes["DP-003"]
assert (c.before_level, c.after_level) == ("unklar", "unauffaellig"), c
print("  ok  DP-003 unklar -> unauffaellig (Messlage, kein Befund)")

print("\nSame level, different facts — what a naive diff would miss")
c = changes["DP-001"]
assert c.kind == SAME_LEVEL_NEW_REASON, c.kind
assert c.before_level == c.after_level == "verdaechtig"
assert "third_party_cookies" in c.before_condition
assert "preselected_checkbox_count" in c.after_condition
assert "anderen Bedingung" in c.note
print("  ok  DP-001 stays eindeutig, but on a different condition")
print(f"      {c.before_condition}  ->  {c.after_condition}")

print("\nUnchanged rules are not reported as changes")
assert all(changes[r].kind == UNCHANGED for r in ("DP-004", "DP-005", "DP-006"))
# DP-003 is a "messlage" change, not a finding — deliberately not noteworthy.
assert [c.rule_id for c in timeline.noteworthy] == ["DP-001", "DP-002"], \
    [c.rule_id for c in timeline.noteworthy]
print("  ok  2 of 6 rules noteworthy")

print("\nSignal level")
changed = {s.signal: s for s in timeline.signal_changes if s.kind == "geaendert"}
assert "countdown_element_present" in changed
assert "preselected_checkbox_count" in changed
assert changed["preselected_checkbox_count"].before == "0"
assert changed["preselected_checkbox_count"].after == "2"
print(f"  ok  {len(changed)} measured values changed, with before and after")
assert all(s.changed for s in timeline.step_changes), \
    "the page state must differ if the measurements do"
print(f"  ok  {len(timeline.step_changes)} page states compared by hash")

print("\nComparing a run with itself")
same = compare(EARLIER, EARLIER, RULES)
assert not same.noteworthy and not same.signal_changes
assert all(not s.changed for s in same.step_changes)
print("  ok  no change is a result, not an error")

print("\nA meaningless comparison says so")
crossed = compare("data/fixtures/viagogo", "data/fixtures/sauberer-shop", RULES)
assert any("verschiedene Ziele" in w for w in crossed.warnings), crossed.warnings
print("  ok  two different sites -> warning")

reversed_order = compare(LATER, EARLIER, RULES)
assert any("vertauscht" in w for w in reversed_order.warnings), reversed_order.warnings
print("  ok  reversed order -> warning")

print("\nHTML")
with tempfile.TemporaryDirectory() as tmp:
    result = build(timeline, output=tmp)
    html = result["html"].read_text(encoding="utf-8")
    assert result["changes"] == 2
    for needle, name in [("Zeitachse", "title"),
                         ("Stufe gleich, Grund anders", "the important case"),
                         ("Geänderte Messwerte", "signal table"),
                         ("Seitenzustand", "hash comparison"),
                         ("Unterlassungserklärung", "enforcement note"),
                         ("keine rechtliche Feststellung", "disclaimer")]:
        assert needle in html, f"missing from the timeline: {name}"
        print(f"  ok  {name}")

print("\nAll timeline tests passed.")
