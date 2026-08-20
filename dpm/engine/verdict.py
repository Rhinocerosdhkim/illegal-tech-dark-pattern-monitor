"""From measured value to verdict level.

    eindeutig       hard to dispute
    verdaechtig     an indication, room for interpretation
    unklar          a required signal was not captured
    unauffaellig    nothing applies
    nicht_anwendbar the rule does not cover this page at all

The level *values* stay German: they are the keys the legal team writes in
rules/*.yaml and the words that appear in the evidence file. Only the
constants around them are English.

"unklar" is not built — it arises on its own, because an uncaptured signal
arrives as MissingSignal.

Behaviour with missing signals, per DECISIONS.md of 20.08. (A3 and
"Bedingungen werden einzeln ausgewertet"):

    Every condition is evaluated INDIVIDUALLY. If one cannot be evaluated,
    only it is skipped and recorded; the rest still apply. If one fires
    afterwards, the finding stands. If none fires and at least one was
    skipped, the verdict is "unklar".

    For applicability there is one addition: if the rule would not fire
    anyway, it is skipped silently. Otherwise every report would carry an
    "unklar" for every rule on every page, and the level would lose its
    meaning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .conditions import (MissingSignal, RuleSyntaxError, SignalTable, evaluate)
from .derivations import is_derived
from .rules import Condition, Rule

CLEAR = "eindeutig"
SUSPECTED = "verdaechtig"
UNRESOLVED = "unklar"
NO_FINDING = "unauffaellig"
NOT_APPLICABLE = "nicht_anwendbar"

YES, NO, UNCERTAIN = "yes", "no", "uncertain"


@dataclass
class Finding:
    rule: Rule
    level: str
    condition: str | None = None
    reason: str | None = None
    evidence: list = field(default_factory=list)   # per signal: value, step, screenshot
    unresolved: list = field(default_factory=list)
    downgraded: bool = False
    would_be_level: str | None = None              # when applicability is open
    notes: list = field(default_factory=list)

    @property
    def reportable(self) -> bool:
        """What belongs in the evidence file."""
        return self.level in (CLEAR, SUSPECTED, UNRESOLVED)


def assess(rule: Rule, table: SignalTable) -> Finding:
    state, open_points, applicability_signals = _applicability(rule, table)

    if state == NO:
        return Finding(rule=rule, level=NOT_APPLICABLE)

    # C4: if applicability is derived rather than established, "eindeutig" is
    # locked. A human confirming the prerequisite in the target profile
    # (confirmed_by_human) unlocks it again.
    derived = [s for s in applicability_signals
               if is_derived(s) and s not in table.confirmed]

    skipped: list = []
    for level in (CLEAR, SUSPECTED):
        for condition in rule.verdict_rules.get(level, []):
            result, gaps = _condition(condition, rule, table)
            if gaps:
                skipped.extend(gaps)
                continue
            if result and result.is_true:
                if state == UNCERTAIN:
                    return _applicability_open(rule, level, condition, open_points)
                return _hit(rule, level, condition, result, table,
                            derived, applicability_signals)

    if skipped:
        return Finding(rule=rule, level=UNRESOLVED, unresolved=_unique(skipped))
    if state == UNCERTAIN:
        # The rule would not fire anyway — pass over it silently rather than
        # filling the file with a meaningless "unklar".
        return Finding(rule=rule, level=NOT_APPLICABLE)
    return Finding(rule=rule, level=NO_FINDING)


def _applicability_open(rule, level, condition, open_points) -> Finding:
    return Finding(
        rule=rule, level=UNRESOLVED, would_be_level=level,
        condition=" ".join(condition.text.split()),
        unresolved=open_points,
        notes=[f"Die Regel wuerde anschlagen ({level}); ob sie auf diese "
               f"Seite ueberhaupt anwendbar ist, konnte nicht geprueft werden."])


def _hit(rule, level, condition, result, table, derived, applicability_signals):
    notes, downgraded = [], False

    if level == CLEAR and derived:
        level = SUSPECTED
        downgraded = True
        notes.append(
            "Herabgestuft auf 'verdaechtig': die Anwendbarkeit stuetzt sich auf "
            "abgeleitete Signale (" + ", ".join(derived) + "), die niemand "
            "bestaetigt hat. Bestaetigung im Zielprofil unter "
            "'confirmed_by_human' hebt die Begrenzung auf.")

    evidence = [e for e in
                (table.evidence(s) for s in
                 _unique(list(result.signals_used) + applicability_signals))
                if e]

    return Finding(rule=rule, level=level,
                   condition=" ".join(condition.text.split()),
                   reason=condition.reason, evidence=evidence,
                   downgraded=downgraded, notes=notes)


def _applicability(rule: Rule, table: SignalTable):
    """(yes | no | uncertain, skipped conditions, signals used)"""
    used: list = []
    open_points: list = []

    def truths(conditions):
        results = []
        for text in conditions:
            evaluation, gaps = _condition(Condition(text=text), rule, table)
            if gaps:
                open_points.extend(gaps)
                continue
            used.extend(evaluation.signals_used)
            results.append(evaluation.is_true)
        return results

    all_of = truths(rule.applies_when.get("all", []))
    any_of = truths(rule.applies_when.get("any", []))
    none_of = truths(rule.applies_when.get("none", []))
    has_any = bool(rule.applies_when.get("any"))

    # If it is already established that a prerequisite fails, that is a
    # statement — not an "unklar".
    if any(r is False for r in all_of) or any(r is True for r in none_of):
        return NO, [], _unique(used)
    if has_any and any(any_of):
        pass                                  # at least one satisfied
    elif has_any and not open_points:
        return NO, [], _unique(used)

    if open_points:
        return UNCERTAIN, _unique(open_points), _unique(used)
    return YES, [], _unique(used)


def _condition(condition: Condition, rule: Rule, table: SignalTable):
    try:
        return evaluate(condition.text, table, rule.lists), None
    except MissingSignal as error:
        return None, [{"signal": error.name, "reason": error.reason}]
    except RuleSyntaxError as error:
        return None, [{"signal": "(Regelwerksfehler)", "reason": str(error)}]


def _unique(items: list) -> list:
    seen, result = set(), []
    for item in items:
        key = item if isinstance(item, str) else tuple(sorted(item.items()))
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
