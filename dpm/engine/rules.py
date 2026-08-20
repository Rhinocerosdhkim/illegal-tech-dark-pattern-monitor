"""Load the rulebook and normalise it.

The rule files are hand-written and currently exist in two spellings (see
docs/ABSTIMMUNG_Regelwerk.md). The engine accepts both and normalises them
here, in one place.

That is deliberate: the legal team should be able to improve its files
without waiting for a format agreement, and we should not be blocked while
that agreement is being reached.

FIELD NAMES. The German field names are the legal team's interface and are
kept as they are — renaming them mid-flight would hit the people writing
them on the deadline day. English aliases are accepted too, so the team can
migrate whenever it suits them. In code the attributes carry English names;
the comment on each shows the YAML key it comes from.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]

LEVELS = ("eindeutig", "verdaechtig")

# YAML key -> attribute. Both spellings are read; the German one is what the
# rule files use today.
_ALIASES = {
    "name": ("name_de", "name"),
    "category": ("kategorie", "category"),
    "author": ("bearbeiter", "author"),
    "legal_test": ("tatbestand_de", "legal_test"),
    "claim_chain": ("anspruchskette", "claim_chain"),
    "explanation_template": ("explanation_template_de", "explanation_template"),
    "human_review": ("menschliche_pruefung", "human_review"),
    "lists": ("listen", "lists"),
}


@dataclass
class Condition:
    text: str
    reason: str | None = None


@dataclass
class Rule:
    id: str
    name: str                                          # name_de
    category: str                                      # kategorie
    status: str
    file: str
    legal_basis: list = field(default_factory=list)
    legal_test: str = ""                               # tatbestand_de
    claim_chain: str = ""                              # anspruchskette
    applies_when: dict = field(default_factory=dict)   # all / any / none
    # C4: set when applicability is INFERRED from facts rather than
    # established (e.g. concluding a Dauerschuldverhaeltnis from a monthly
    # price). Such a rule may reach at most "verdaechtig". Site-wide
    # prerequisites can be lifted per target via confirmed_by_human;
    # product-dependent ones cannot, which is why the rule declares it.
    applicability_derived: bool = False
    verdict_rules: dict = field(default_factory=dict)  # level -> [Condition]
    lists: dict = field(default_factory=dict)          # listen
    explanation_template: str = ""                     # explanation_template_de
    threshold_source: str = ""
    false_positive_risks: list = field(default_factory=list)
    human_review: list = field(default_factory=list)   # menschliche_pruefung
    disclaimer_required: bool = True

    @property
    def norm(self) -> str:
        """First provision cited — what goes into the findings table."""
        return self.legal_basis[0] if self.legal_basis else "—"


def load_rules(directory: str | Path | None = None) -> list:
    """Load rules/*.yaml.

    The default path deliberately does not depend on the working directory.
    Called from elsewhere, glob() would find nothing, zero rules would load,
    and the evidence file would report "0 findings" without comment — the
    most dangerous possible result.
    """
    directory = Path(directory) if directory else ROOT / "rules"
    rules = []
    for path in sorted(directory.glob("*.yaml")):
        if path.name.startswith("_"):        # _VORLAGE.yaml is not a rule
            continue
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
        for raw in content if isinstance(content, list) else [content]:
            if isinstance(raw, dict) and raw.get("id"):
                rules.append(_build(raw, path.name))
    if not rules:
        raise FileNotFoundError(
            f"{directory} contains no rule at all. Without a rulebook "
            f"nothing can be checked.")
    return rules


def _pick(raw: dict, attribute: str, default=None):
    for key in _ALIASES[attribute]:
        if raw.get(key) is not None:
            return raw[key]
    return default


def _build(raw: dict, filename: str) -> Rule:
    return Rule(
        id=raw["id"],
        name=_pick(raw, "name", raw["id"]),
        category=_pick(raw, "category", "—"),
        status=raw.get("status", "ENTWURF"),
        file=filename,
        legal_basis=list(raw.get("legal_basis") or []),
        legal_test=str(_pick(raw, "legal_test", "")).strip(),
        claim_chain=str(_pick(raw, "claim_chain", "")).strip(),
        applies_when=_applies_when(raw.get("applies_when")),
        applicability_derived=bool(raw.get("applicability_derived", False)),
        verdict_rules=_verdict_rules(raw.get("verdict_rules")),
        lists=_lists(_pick(raw, "lists")),
        explanation_template=str(_pick(raw, "explanation_template", "")).strip(),
        threshold_source=(raw.get("threshold_source") or "").strip(),
        false_positive_risks=[str(r).strip()
                              for r in (raw.get("false_positive_risks") or [])],
        human_review=list(_pick(raw, "human_review", []) or []),
        disclaimer_required=bool(raw.get("disclaimer_required", True)),
    )


def _applies_when(raw) -> dict:
    """Bring a flat list and the all/any/none form into one shape."""
    empty = {"all": [], "any": [], "none": []}
    if not raw:
        return empty
    if isinstance(raw, list):
        return {**empty, "all": [str(c) for c in raw]}
    return {key: [str(c) for c in (raw.get(key) or [])] for key in empty}


def _lists(raw) -> dict:
    """Named word lists for the operators 'in' and 'not in'.

    This is how the legal team maintains permitted and impermissible
    button labels without anyone programming (_VORLAGE.yaml, LISTEN).
    """
    if not isinstance(raw, dict):
        return {}
    return {name: [str(e) for e in (entries or [])]
            for name, entries in raw.items()}


def _verdict_rules(raw) -> dict:
    """Accept both the string form and the object form.

    'severity' is deliberately ignored: a second severity scale next to
    eindeutig/verdaechtig/unklar would be a source of error and would have
    to be explained and defended in the presentation
    (ABSTIMMUNG_Regelwerk.md §2). 'reason' is kept — a justification per
    condition is valuable for the evidence file.
    """
    result = {level: [] for level in LEVELS}
    for level in LEVELS:
        for entry in (raw or {}).get(level) or []:
            if isinstance(entry, dict):
                result[level].append(Condition(
                    text=str(entry.get("condition", "")),
                    reason=(entry.get("reason") or "").strip() or None))
            else:
                result[level].append(Condition(text=str(entry)))
    return result
