"""Zeitachse — comparing two captures of the same site.

This is what separates a scanner from a monitor, and it is the third of the
three arguments the presentation rests on. The challenge asks for it in so
many words: "documents changes over time".

Its practical value for a consumer protection agency is enforcement. A
company that gave a cease-and-desist undertaking (Unterlassungserklärung)
and then quietly reintroduces the design owes a contractual penalty — but
only if somebody notices. Noticing is exactly this comparison.

No database. A capture run is one JSON file; the timeline is a comparison
of two of them.

Three kinds of change matter, and the third is the one a naive diff misses:

    a finding disappears        the design was corrected
    a finding appears           new, or quietly reintroduced
    the level stays the same    but rests on completely different facts

The third is why this compares SIGNALS, not just verdict levels. A banner
that stops tracking before consent but starts pre-ticking checkboxes is
still "eindeutig" — and reporting "unverändert" would be wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from dpm import PRODUCT_NAME
from dpm.engine.rules import load_rules
from dpm.engine.run import Run, load_run
from dpm.engine.verdict import (CLEAR, NOT_APPLICABLE, NO_FINDING, SUSPECTED,
                                UNRESOLVED, assess)
from dpm.report.case_file import CATEGORY_LABEL, LEVEL_LABEL, _environment

# How far apart two levels are. "unklar" deliberately sits between silence
# and a finding: it is not a stronger statement than "unauffaellig", but it
# is not the same either.
RANK = {NOT_APPLICABLE: 0, NO_FINDING: 0, UNRESOLVED: 1, SUSPECTED: 2, CLEAR: 3}

NEW = "neu"
RESOLVED = "behoben"
WORSE = "verschaerft"
BETTER = "entschaerft"
SAME_LEVEL_NEW_REASON = "grund_geaendert"
MEASUREMENT = "messlage"
UNCHANGED = "unveraendert"

KIND_LABEL = {
    NEW: "neu",
    RESOLVED: "behoben",
    WORSE: "verschärft",
    BETTER: "entschärft",
    SAME_LEVEL_NEW_REASON: "Stufe gleich, Grund anders",
    MEASUREMENT: "Messlage geändert",
    UNCHANGED: "unverändert",
}

# What a person has to look at. "unveraendert" is not one of them.
NOTEWORTHY = (NEW, RESOLVED, WORSE, BETTER, SAME_LEVEL_NEW_REASON)


@dataclass
class RuleChange:
    rule_id: str
    rule_name: str
    category: str
    norm: str
    before_level: str
    after_level: str
    kind: str
    before_condition: str = ""
    after_condition: str = ""
    note: str = ""


@dataclass
class SignalChange:
    signal: str
    kind: str                 # geaendert | neu_erhoben | nicht_mehr_erhoben
    before: str = ""
    after: str = ""
    step: str = ""


@dataclass
class StepChange:
    step: str
    before_hash: str
    after_hash: str
    changed: bool


@dataclass
class Timeline:
    earlier: Run
    later: Run
    rule_changes: list = field(default_factory=list)
    signal_changes: list = field(default_factory=list)
    step_changes: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def noteworthy(self) -> list:
        return [c for c in self.rule_changes if c.kind in NOTEWORTHY]

    @property
    def days_between(self) -> str:
        return f"{self.earlier.meta.get('timestamp', '?')[:10]} → " \
               f"{self.later.meta.get('timestamp', '?')[:10]}"


def compare(earlier_path, later_path, rules=None) -> Timeline:
    rules = rules or load_rules()
    earlier, later = load_run(earlier_path), load_run(later_path)

    timeline = Timeline(earlier=earlier, later=later)

    # Comparing two different sites produces a diff that looks plausible and
    # means nothing. Say so loudly rather than quietly returning nonsense.
    if earlier.target != later.target:
        timeline.warnings.append(
            f"Die beiden Erfassungen betreffen verschiedene Ziele "
            f"({earlier.target} und {later.target}). Ein Vergleich ist "
            f"insoweit ohne Aussagekraft.")
    if (earlier.meta.get("timestamp") or "") > (later.meta.get("timestamp") or ""):
        timeline.warnings.append(
            "Die erste Erfassung liegt zeitlich nach der zweiten. Die "
            "Reihenfolge der Argumente ist vermutlich vertauscht.")
    if earlier.meta.get("viewport") != later.meta.get("viewport"):
        timeline.warnings.append(
            "Die beiden Erfassungen verwenden verschiedene Fenstergrößen. "
            "Pixelflächen sind dann nicht vergleichbar.")

    before = {f.rule.id: f for f in (assess(r, earlier.table) for r in rules)}
    after = {f.rule.id: f for f in (assess(r, later.table) for r in rules)}

    for rule in rules:
        timeline.rule_changes.append(_rule_change(rule, before[rule.id],
                                                  after[rule.id]))

    timeline.signal_changes = _signal_changes(earlier, later)
    timeline.step_changes = _step_changes(earlier, later)
    return timeline


def _rule_change(rule, before, after) -> RuleChange:
    kind, note = _classify(before, after)
    return RuleChange(
        rule_id=rule.id, rule_name=rule.name,
        category=CATEGORY_LABEL.get(rule.category, rule.category),
        norm=rule.norm,
        before_level=before.level, after_level=after.level, kind=kind,
        before_condition=before.condition or "",
        after_condition=after.condition or "", note=note)


def _classify(before, after):
    was_finding = before.level in (CLEAR, SUSPECTED)
    is_finding = after.level in (CLEAR, SUSPECTED)

    if before.level == after.level:
        if was_finding and before.condition != after.condition:
            return SAME_LEVEL_NEW_REASON, (
                "Die Stufe ist unverändert, sie beruht jetzt aber auf einer "
                "anderen Bedingung. Der frühere Befund ist behoben, an seine "
                "Stelle ist ein neuer getreten.")
        return UNCHANGED, ""

    if UNRESOLVED in (before.level, after.level) and not (was_finding or is_finding):
        return MEASUREMENT, (
            "Ein Signal war beim einen Lauf messbar und beim anderen nicht. "
            "Das ist keine Aussage über die Seite, sondern über die Erfassung.")

    if not was_finding and is_finding:
        return NEW, ("Auf dieser Seite war zuvor nichts zu beanstanden. "
                     "Falls hierzu eine Unterlassungserklärung vorliegt, ist "
                     "das der Zeitpunkt, sie zu prüfen.")
    if was_finding and not is_finding:
        return RESOLVED, "Der frühere Befund ist nicht mehr feststellbar."

    return (WORSE, "") if RANK[after.level] > RANK[before.level] else (BETTER, "")


def _signal_changes(earlier: Run, later: Run) -> list:
    changes = []
    for name in sorted(set(earlier.table.values) | set(later.table.values)):
        a, b = earlier.table.values.get(name), later.table.values.get(name)
        if a and b:
            if a["value"] != b["value"]:
                changes.append(SignalChange(
                    signal=name, kind="geaendert",
                    before=_show(a["value"]), after=_show(b["value"]),
                    step=b.get("step") or a.get("step") or ""))
        elif b:
            changes.append(SignalChange(signal=name, kind="neu_erhoben",
                                        after=_show(b["value"]),
                                        step=b.get("step") or ""))
        else:
            changes.append(SignalChange(signal=name, kind="nicht_mehr_erhoben",
                                        before=_show(a["value"]),
                                        step=a.get("step") or ""))
    return changes


def _step_changes(earlier: Run, later: Run) -> list:
    later_steps = {s["step"]: s for s in later.steps}
    changes = []
    for step in earlier.steps:
        other = later_steps.get(step["step"])
        if not other:
            continue
        before, after = step.get("dom_hash", ""), other.get("dom_hash", "")
        changes.append(StepChange(step=step["step"], before_hash=before,
                                  after_hash=after, changed=before != after))
    return changes


def _show(value) -> str:
    if isinstance(value, bool):
        return "ja" if value else "nein"
    return f"„{value}“" if isinstance(value, str) else str(value)


def build(timeline: Timeline, output: str | Path = "out") -> dict:
    folder = Path(output) / f"zeitachse_{timeline.later.run_id}"
    folder.mkdir(parents=True, exist_ok=True)

    html = _environment().get_template("zeitachse.html").render(
        produkt=PRODUCT_NAME,
        zeitachse=timeline,
        aenderungen=timeline.rule_changes,
        bemerkenswert=timeline.noteworthy,
        signale=timeline.signal_changes,
        schritte=timeline.step_changes,
        art_label=KIND_LABEL,
        stufe_label=LEVEL_LABEL,
        warnungen=timeline.warnings + timeline.earlier.warnings
        + timeline.later.warnings,
    )
    path = folder / "zeitachse.html"
    path.write_text(html, encoding="utf-8")
    return {"html": path, "changes": len(timeline.noteworthy)}
