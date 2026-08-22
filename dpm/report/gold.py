"""System verdict against human verdict.

The strategy paper calls the false-alarm rate "the more important number",
and it is the question the consumer agency will ask first: how often does
this thing claim something that is not there. A demonstration answers
"look what it found"; only this answers "and how often is it wrong".

Three things this deliberately does NOT do.

`unklar` is not counted as a mistake. The level means "we could not
measure it" — it asserts nothing, so it can be neither right nor wrong.
Folding it into the error rate would punish the system for being honest,
and folding it into the hit rate would let it claim findings it never
made. It is reported on its own line.

A gold row without a capture is not silently dropped. It is reported as
uncovered, because "we agreed on the nine sites we happened to capture"
is a different statement from "we agreed on nine of twenty".

Nothing is aggregated across rules for a site. § 25 TDDDG and § 312j BGB
are separate assessments; averaging them produces a number that means
nothing.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from dpm.engine.verdict import (CLEAR, NOT_APPLICABLE, NO_FINDING, SUSPECTED,
                                UNRESOLVED)

GOLD = Path("data/gold-standard/gold-standard.csv")

# What the humans write, mapped onto the engine's levels. The gold standard
# knows three answers; the engine's "unklar" has no human counterpart, by
# design — a person does not record "could not measure".
HUMAN = {"eindeutig": CLEAR, "verdaechtig": SUSPECTED,
         "verdächtig": SUSPECTED, "unauffaellig": NO_FINDING,
         "unauffällig": NO_FINDING}

# A finding is "asserted" when the system claims something about the site.
ASSERTED = (CLEAR, SUSPECTED)

# The system said nothing about this rule on this site. "nicht_anwendbar"
# belongs here as much as "unauffaellig" does: it is an assertion — the rule
# does not apply — and if a person found a violation of exactly that rule,
# we were silent about it. Counting only "unauffaellig" made the miss rate
# better the more often a rule excluded itself.
SILENT = (NO_FINDING, NOT_APPLICABLE)


@dataclass
class Comparison:
    rows: list = field(default_factory=list)      # matched pairs
    uncovered: list = field(default_factory=list)  # gold rows with no capture
    unreadable: list = field(default_factory=list)  # rows we could not use
    fixtures_ignored: int = 0                     # hand-written, not measured

    @property
    def agreed(self) -> list:
        return [r for r in self.rows if r["human"] == r["system"]]

    @property
    def false_alarms(self) -> list:
        """System asserts a finding, the human found nothing."""
        return [r for r in self.rows
                if r["system"] in ASSERTED and r["human"] == NO_FINDING]

    @property
    def missed(self) -> list:
        """The human found something, the system stayed silent about it."""
        return [r for r in self.rows
                if r["human"] in ASSERTED and r["system"] in SILENT]

    @property
    def unresolved(self) -> list:
        """Not measurable — neither a hit nor a mistake."""
        return [r for r in self.rows if r["system"] == UNRESOLVED]

    @property
    def decided(self) -> list:
        """The rows a rate may be computed over."""
        return [r for r in self.rows if r["system"] != UNRESOLVED]

    @property
    def clean(self) -> list:
        """Decided rows the human marked as unremarkable.

        This is the denominator of the false-alarm rate: of the sites where
        there was nothing to find, how often did we claim otherwise. Divided
        by all rows instead, the number improves whenever more guilty sites
        are added to the sample — which would be meaningless.

        Rows where the rule excluded itself are out as well. A rule that
        does not apply cannot raise a false alarm, so counting it in the
        denominator improves the rate for free — point DP-004 at enough
        shops without a subscription and the figure approaches zero without
        the system getting any better. What the number should say is: of
        the cases where the rule was in play and there was nothing to find,
        how often did we claim otherwise.
        """
        return [r for r in self.decided
                if r["human"] == NO_FINDING and r["system"] != NOT_APPLICABLE]

    @property
    def flagged_by_human(self) -> list:
        """Decided rows where the human did find something."""
        return [r for r in self.decided if r["human"] in ASSERTED]

    @property
    def deviations(self) -> list:
        return [r for r in self.decided if r["human"] != r["system"]]


def domain(value: str) -> str:
    """Compare sites by host, ignoring scheme, www and trailing slashes."""
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    if "://" not in raw:
        raw = "https://" + raw
    host = urlparse(raw).netloc or ""
    return host[4:] if host.startswith("www.") else host


def read(path: str | Path = GOLD) -> list:
    """Rows of the gold standard, as written by the legal team."""
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle)
                if any((value or "").strip() for value in row.values())]


def compare(gold_rows: list, overview_rows: list, runs: list) -> Comparison:
    """Match each gold row to the run of the same site and the same rule."""
    # A site captured twice must be compared against ONE capture, and the
    # sensible one is the most recent: the human judged the site as it is
    # now. Picking whichever run was found first would silently compare
    # against a state nobody looked at.
    # A fixture is a capture we wrote by hand, carrying the verdicts we
    # wanted to see. Held against a human verdict it measures nothing but
    # our own consistency, and it does worse than that: it displaces the
    # real capture of the same site, because "most recent wins" and
    # viagogo-2026-09 is dated in the future. Filtered here and not at the
    # call site, so that no caller can put them back by forgetting.
    real = [run for run in runs
            if (run.meta.get("capture_mode") or "") != "fixture"]

    captured = {}
    for run in real:
        key = domain(run.meta.get("start_url") or "") or (run.target or "")
        current = captured.get(key)
        if current is None or str(run.meta.get("timestamp") or "") > str(
                current.meta.get("timestamp") or ""):
            captured[key] = run

    by_run_rule = {(row.run_id, row.rule_id): row for row in overview_rows}

    result = Comparison(fixtures_ignored=len(runs) - len(real))
    for gold in gold_rows:
        human = HUMAN.get((gold.get("befund_mensch") or "").strip().lower())
        rule = (gold.get("pattern_id") or "").strip().upper()
        site = domain(gold.get("url") or "")
        if human is None or not rule or not site:
            result.unreadable.append(gold)
            continue

        run = captured.get(site)
        row = by_run_rule.get((run.run_id, rule)) if run else None
        if row is None:
            result.uncovered.append({"site": site, "rule": rule,
                                     "human": human, "gold": gold})
            continue

        result.rows.append({"site": site, "rule": rule, "human": human,
                            "system": row.level, "run_id": row.run_id,
                            "note": (gold.get("notiz") or "").strip()})
    return result


def rate(part: list, whole: list) -> str:
    """A share, written so it cannot be read as more precise than it is."""
    if not whole:
        return "—"
    return f"{len(part)}/{len(whole)} ({round(100 * len(part) / len(whole))} %)"
