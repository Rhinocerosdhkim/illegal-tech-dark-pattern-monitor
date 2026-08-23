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

import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from dpm import PRODUCT_NAME
from dpm.engine.rules import load_rules
from dpm.engine.run import Run, load_run
from dpm.engine.verdict import (CLEAR, NOT_APPLICABLE, NO_FINDING, SUSPECTED,
                                UNRESOLVED, assess)
from dpm.report.case_file import CATEGORY_LABEL, LEVEL_LABEL, _environment
from dpm.report.pdf import render as render_pdf

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
        """What a person has to look at.

        A change in measurability counts when a finding stands on either
        side: "we can no longer reproduce this" and "this is measurable
        now" both need a decision, even though neither says the site
        changed. Between two levels that assert nothing it is noise.
        """
        return [c for c in self.rule_changes
                if c.kind in NOTEWORTHY
                or (c.kind == MEASUREMENT
                    and {c.before_level, c.after_level} & {CLEAR, SUSPECTED})]

    @property
    def days_between(self) -> str:
        return f"{self.earlier.meta.get('timestamp', '?')[:10]} → " \
               f"{self.later.meta.get('timestamp', '?')[:10]}"

    @property
    def days(self) -> int | None:
        """Days between the two captures, or None if a date is unusable.

        The gap is what makes a timeline readable — "the countdown came
        back after 104 days" says more than two dates do.
        """
        try:
            earlier = date.fromisoformat(
                str(self.earlier.meta.get("timestamp"))[:10])
            later = date.fromisoformat(
                str(self.later.meta.get("timestamp"))[:10])
        except (TypeError, ValueError):
            return None
        return (later - earlier).days


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

    # "unklar" is not a statement about the site, it says a value could not
    # be measured. Comparing a statement with a non-statement cannot produce
    # a statement about the site -- so every transition involving it is a
    # change in what we could measure, whichever side it sits on.
    #
    # The gate used to require that NEITHER side was a finding, which left
    # "verdaechtig -> unklar" falling through to RESOLVED: a site that
    # merely stopped being measurable was reported as having fixed the
    # violation, and the reverse arrived as "neu" with the note about a
    # Unterlassungserklaerung. In an enforcement file that is backwards.
    if UNRESOLVED in (before.level, after.level):
        if was_finding:
            return MEASUREMENT, (
                "Der frühere Befund ist nicht widerlegt — er ließ sich diesmal "
                "nur nicht mehr messen. Das ist keine Feststellung darüber, "
                "dass die Seite geändert wurde.")
        if is_finding:
            return MEASUREMENT, (
                "Beim früheren Lauf war dies nicht messbar. Der Befund steht "
                "für sich; ob er damals schon zutraf, sagt der Vergleich "
                "nicht.")
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


def _evidence_pairs(timeline: Timeline, folder: Path) -> list:
    """Both captures of the same step, side by side.

    Copied under prefixed names because the two runs use the same file
    names. Only steps present in both runs are shown — a step that exists
    on one side only is not a comparison.
    """
    later_steps = {s.get("step"): s for s in timeline.later.steps
                   if isinstance(s, dict)}
    changed = {c.step: c.changed for c in timeline.step_changes}
    pairs = []
    for step in timeline.earlier.steps:
        name = step.get("step") if isinstance(step, dict) else None
        other = later_steps.get(name)
        if not other:
            continue
        pair = {"step": name, "changed": changed.get(name, False),
                "frueher": None, "spaeter": None,
                "frueher_hash": step.get("dom_hash"),
                "spaeter_hash": other.get("dom_hash")}
        for key, run, source in (("frueher", timeline.earlier, step),
                                 ("spaeter", timeline.later, other)):
            image = run.screenshot(source.get("screenshot"))
            if image:
                target = folder / f"{key}_{image.name}"
                shutil.copyfile(image, target)
                pair[key] = target.name
        pairs.append(pair)
    return pairs


def build(timeline: Timeline, output: str | Path = "out",
          as_pdf: bool = False) -> dict:
    folder = Path(output) / f"zeitachse_{timeline.later.run_id}"
    folder.mkdir(parents=True, exist_ok=True)

    paare = _evidence_pairs(timeline, folder)

    html = _environment().get_template("zeitachse.html").render(
        produkt=PRODUCT_NAME,
        zeitachse=timeline,
        aenderungen=timeline.rule_changes,
        bemerkenswert=timeline.noteworthy,
        signale=timeline.signal_changes,
        schritte=timeline.step_changes,
        paare=paare,
        art_label=KIND_LABEL,
        stufe_label=LEVEL_LABEL,
        warnungen=timeline.warnings + timeline.earlier.warnings
        + timeline.later.warnings,
    )
    path = folder / "zeitachse.html"
    path.write_text(html, encoding="utf-8")
    # A timeline is what you attach when a company reintroduced a design it
    # had undertaken to stop using. That has to be a document, not a tab.
    pdf = render_pdf(path) if as_pdf else None
    return {"html": path, "pdf": pdf, "changes": len(timeline.noteworthy)}
