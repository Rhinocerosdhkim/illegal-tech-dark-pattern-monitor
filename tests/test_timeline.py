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
for rule_id in ("DP-002", "DP-003"):
    c = changes[rule_id]
    assert (c.kind, c.before_level, c.after_level) == (RESOLVED, "verdaechtig", "unauffaellig"), c
    assert c.before_condition and not c.after_condition
    print(f"  ok  {rule_id} verdaechtig -> unauffaellig, earlier condition recorded")

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
assert [c.rule_id for c in timeline.noteworthy] == ["DP-001", "DP-002", "DP-003"], \
    [c.rule_id for c in timeline.noteworthy]
print("  ok  3 of 6 rules noteworthy")

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
    assert result["changes"] == 3
    for needle, name in [("Zeitachse", "title"),
                         ("Stufe gleich, Grund anders", "the important case"),
                         # Renamed with the design handoff (view #1e); the
                         # hash comparison now sits with the two screenshots
                         # of the step instead of in a table of its own.
                         ("Signalvergleich", "signal table"),
                         ("Seitenzustand", "hash comparison"),
                         ("Unterlassungserklärung", "enforcement note"),
                         ("keine rechtliche Feststellung", "disclaimer")]:
        assert needle in html, f"missing from the timeline: {name}"
        print(f"  ok  {name}")

print("\n'unklar' on either side is a measurement change, never a verdict")

from dpm.report.diff import (KIND_LABEL, MEASUREMENT, RuleChange, Timeline,
                             _classify)
from dpm.engine.verdict import CLEAR, NO_FINDING, SUSPECTED, UNRESOLVED


class _Side:
    def __init__(self, level):
        self.level, self.condition = level, "eine Bedingung"


# A site that merely stopped being measurable used to be reported as having
# fixed the violation, and the reverse arrived as "neu" with the note about
# a Unterlassungserklaerung. In an enforcement file that is backwards.
for before, after, why in [
        (SUSPECTED, UNRESOLVED, "a finding that became unmeasurable"),
        (CLEAR, UNRESOLVED, "the same from the top level"),
        (UNRESOLVED, SUSPECTED, "a finding that became measurable"),
        (UNRESOLVED, NO_FINDING, "neither side asserts anything")]:
    kind, note = _classify(_Side(before), _Side(after))
    assert kind == MEASUREMENT, f"{why}: {KIND_LABEL[kind]}"
    assert note, why
    assert "behoben" not in note and "Unterlassungserkl" not in note, note
    print(f"  ok  {before} -> {after}: {KIND_LABEL[kind]}")

# The genuine transitions must keep their meaning.
assert _classify(_Side(SUSPECTED), _Side(NO_FINDING))[0] == "behoben"
assert _classify(_Side(NO_FINDING), _Side(SUSPECTED))[0] == "neu"
print("  ok  measured transitions are still behoben / neu")

# ...and widening the gate must not drop them out of what a person sees.
def _change(before, after):
    return RuleChange(rule_id="DP-X", rule_name="x", category="c", norm="n",
                      before_level=before, after_level=after,
                      kind=_classify(_Side(before), _Side(after))[0])

seen = Timeline(earlier=None, later=None, rule_changes=[
    _change(SUSPECTED, UNRESOLVED), _change(UNRESOLVED, SUSPECTED),
    _change(UNRESOLVED, NO_FINDING)])
kinds = [(c.before_level, c.after_level) for c in seen.noteworthy]
assert (SUSPECTED, UNRESOLVED) in kinds, "a lost finding vanished from the list"
assert (UNRESOLVED, SUSPECTED) in kinds, "a newly measurable finding vanished"
assert (UNRESOLVED, NO_FINDING) not in kinds, "noise was promoted to noteworthy"
print("  ok  both finding-side cases stay visible, the noise does not")


print("\nAll timeline tests passed.")
