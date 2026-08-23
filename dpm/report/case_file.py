"""Beweisakte — one site, one procedure, as a PDF.

The output is deliberately not called a "report". The consumer agency used
the word "Beweisakte" in the seminar of 19.08., and the difference is
substantive: every finding points at a screenshot, a DOM hash and a point
in time. What is not backed by evidence does not appear.

The rendered document stays German — it is the deliverable for a German
consumer protection agency and may be attached to a formal warning letter.
The code around it is English.

Structure:
    header            target, capture conditions, reproducibility
    findings table    the overview a warning letter is built from
    per finding       provision, legal test, measured values, claim chain,
                      origin of thresholds, false-alarm risks
    not verifiable    what we could NOT establish, with the reason
    capture log       steps with hashes
    notice            liability safeguard
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import (ChainableUndefined, Environment, FileSystemLoader,
                    select_autoescape)

from dpm import PRODUCT_NAME
from dpm.engine.conditions import MissingSignal, SignalTable
from dpm.engine.run import Run
from dpm.engine.rules import Rule
from dpm.engine.verdict import CLEAR, SUSPECTED, UNRESOLVED, Finding
from dpm.report.design import fonts
from dpm.report.pdf import footer, render as render_pdf

LEVEL_LABEL = {CLEAR: "eindeutig", SUSPECTED: "verdächtig",
               UNRESOLVED: "unklar", "unauffaellig": "unauffällig",
               "nicht_anwendbar": "nicht anwendbar"}

_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

# Markers the legal team left in a text that is still being written:
# [CHECKOUT_PRICE], or the conditional form {signal == value, default: '...'}
# that the rulebook proposes and no engine implements. They are looked for
# AFTER substitution, so every {name} that stands for a measurement is gone
# by then and whatever braces remain were never going to resolve.
_UNFINISHED = re.compile(r"\[[A-Z][A-Z0-9_]{2,}\]|\{[^{}]*\}")

# Printed instead of the text. Better openly unfinished than quietly wrong:
# the placeholders themselves went into the PDF before this.
INCOMPLETE_TEXT = (
    "Der Erlaeuterungstext dieser Regel ist im Regelwerk noch nicht "
    "vollstaendig — er enthaelt Platzhalter, die sich nicht aufloesen "
    "lassen, und wird deshalb hier nicht wiedergegeben. Der Befund, die "
    "zutreffende Bedingung und die Messwerte stehen unveraendert oben.")

# Order in which the levels are counted out wherever a run is summarised.
LEVEL_CLASS_ORDER = [(CLEAR, "eindeutig"), (SUSPECTED, "verdaechtig"),
                     (UNRESOLVED, "unklar")]

# The rulebook writes the categories without umlauts. In a document that
# accompanies a warning letter, the correct spelling belongs.
CATEGORY_LABEL = {"Irrefuehrung": "Irreführung", "Zeitdruck": "Zeitdruck",
                  "Zwang": "Zwang", "Hindernisse": "Hindernisse"}

# The binding wording comes from packet 3 of the legal team. Until then a
# visibly provisional text stands here — better openly unfinished than
# quietly invented.
PROVISIONAL_NOTICE = (
    "PLATZHALTER — der verbindliche Wortlaut steht aus (Paket 3). "
    f"{PRODUCT_NAME} stellt technisch messbare Tatsachen fest und ordnet sie "
    "einem Regelwerk zu. Es trifft keine rechtliche Feststellung eines "
    "Verstoßes. Die rechtliche Bewertung obliegt der prüfenden Person."
)


@dataclass
class CaseFile:
    html: Path
    pdf: Path | None
    finding_count: int
    # Problems with the rulebook rather than with the capture. Printed by
    # the command, because a document that silently drops a paragraph looks
    # exactly like one that never had it.
    warnings: list = field(default_factory=list)


def build(run: Run, findings: list, output: str | Path = "out",
          as_pdf: bool = True, summaries: dict | None = None) -> CaseFile:
    """Write the Beweisakte.

    `summaries` maps a rule id to a machine-formulated paragraph (AI ④).
    It is empty by default and the document is complete without it: what
    carries a finding is the rulebook's own text, not a model's.
    """
    folder = Path(output) / run.run_id
    folder.mkdir(parents=True, exist_ok=True)

    reportable = [f for f in findings if f.reportable]
    steps = step_index(run)

    for name in _screenshot_names(reportable, run):
        source = run.screenshot(name)
        # A live capture writes into out/<run_id>/ and the Beweisakte is
        # built into the same folder, so source and target are then one
        # file. Copying it onto itself raises; there is also nothing to do.
        if source and not source.resolve() == (folder / name).resolve():
            shutil.copyfile(source, folder / name)

    eintraege = [_entry(nr, f, steps, run, folder, summaries or {})
                 for nr, f in enumerate(reportable, start=1)]

    html = _environment().get_template("beweisakte.html").render(
        produkt=PRODUCT_NAME,
        lauf=run,
        meta=run.meta,
        schritte=run.steps,
        hinweis=PROVISIONAL_NOTICE,
        zusammenfassung=_summary(findings),
        eintraege=eintraege,
        kategorie=CATEGORY_LABEL,
        warnungen=run.warnings,
        kennzahlen=_key_figures(run, findings, eintraege),
        regelanzahl=len(findings),
        nachweise=_all_evidence(eintraege),
    )

    target_html = folder / "beweisakte.html"
    target_html.write_text(html, encoding="utf-8")

    running = footer(f"{PRODUCT_NAME} · {len(findings)} Regeln · "
                     f"{run.run_id} · lokal erzeugt")
    pdf = render_pdf(target_html, running_footer=running) if as_pdf else None
    return CaseFile(html=target_html, pdf=pdf, finding_count=len(reportable),
                    warnings=[e["unfertiger_text"] for e in eintraege
                              if e["unfertiger_text"]])


# --- preparation ---------------------------------------------------------

def _entry(nr: int, finding: Finding, steps: dict, run: Run,
           folder: Path, summaries: dict | None = None) -> dict:
    evidence = [_evidence(e, steps) for e in finding.evidence]
    erlaeuterung, unfertig = _explanation(finding, run.table)
    # The note goes where the reader is already looking for caveats, and it
    # names the rule, so nobody has to guess which text is missing.
    hinweise = [*finding.notes, INCOMPLETE_TEXT] if unfertig else finding.notes
    return {
        "nr": nr,
        "regel": finding.rule,
        "stufe": LEVEL_LABEL[finding.level],
        "stufe_code": finding.level,
        "bedingung": finding.condition,
        "begruendung": finding.reason,
        "herabgestuft": finding.downgraded,
        "hinweise": hinweise,
        "unklar_wegen": finding.unresolved,
        "wuerde_stufe": LEVEL_LABEL.get(finding.would_be_level or ""),
        "nachweise": evidence,
        "messwerte": ", ".join(f"{e['signal']} = {_short(e['value'])}"
                               for e in evidence) or "—",
        "screenshots": _images(evidence, folder),
        "erlaeuterung": erlaeuterung,
        "unfertiger_text": unfertig,
        "zusammenfassung": (summaries or {}).get(finding.rule.id),
    }


def step_index(run) -> dict:
    """Look up a step by its screenshot, and only then by its name.

    Two steps can carry the same name: a walk may pass the start page
    twice, and since a signal keeps the step it was really measured on, its
    evidence may point at the earlier of them. Keyed by name alone, the
    last step of that name won, and the Beweisakte printed its hash and its
    address under the screenshot of the first. In an evidence document the
    hash is what proves that this image shows that page state, so it has to
    belong to the image beside it.
    """
    index = {s["step"]: s for s in run.steps
             if isinstance(s, dict) and s.get("step")}
    index.update({s["screenshot"]: s for s in run.steps
                  if isinstance(s, dict) and s.get("screenshot")})
    return index


def _evidence(raw: dict, steps: dict) -> dict:
    label = raw.get("step")
    step = steps.get(raw.get("evidence")) or steps.get(label) or {}
    return {**raw,
            "display": _short(raw.get("value")),
            "url": step.get("url"),
            # If the step is missing from the log, reproducibility is not
            # documented. That has to say so, not show a dash.
            "dom_hash": step.get("dom_hash") or (
                "—" if label == "Zielprofil"
                else "Schritt nicht im Erfassungsprotokoll")}


def _images(evidence: list, folder: Path) -> list:
    """Only screenshots that actually sit next to the file.

    An evidence file that points at an image which does not exist asserts a
    piece of evidence that does not exist.
    """
    seen, images = set(), []
    for e in evidence:
        name = e.get("evidence")
        if not isinstance(name, str) or not name.lower().endswith(".png"):
            continue
        if name in seen:
            continue
        seen.add(name)
        images.append({"datei": name, "schritt": e.get("step"),
                       "dom_hash": e.get("dom_hash"),
                       "vorhanden": (folder / name).exists()})
    return images


def _explanation(finding: Finding, table: SignalTable) -> tuple:
    """Pick the text for THIS finding's level, then substitute placeholders.

    Returns (text, problem). `problem` is None when the text is usable.

    The template is chosen per verdict level. A "verdaechtig" finding must
    not be explained with a sentence that asserts the requirement was not
    met — that would claim more than the level does
    (docs/BEFUNDSTUFEN.md 6). Rules that give a single text keep it under
    the key "*".

    That "*" is NOT used at "unklar". The level asserts nothing at all —
    it means a value could not be measured — so any narrative describing a
    measurement claims more than the finding does. DP-005 printed its
    checkout-price text directly under "Nicht erhoben — deshalb keine
    Feststellung" on the clean reference shop. A rule that wants to say
    something at "unklar" gives it an explicit "unklar" template, as
    DP-006 does.

    {befund} is replaced by the reason of the condition that fired.

    The whole signal table is queried, not just the signals of the matching
    condition: the explanatory text regularly names measurements that
    merely put the finding in context.

    "[nicht erhoben]" appears only where nothing was actually measured. In
    a document that accompanies a warning letter, claiming something was
    not captured when it was would be a factual error.
    """
    templates = finding.rule.explanation_template
    template = templates.get(finding.level)
    if template is None and finding.level != UNRESOLVED:
        template = templates.get("*")
    if not template:
        return "", None

    def substitute(match):
        name = match.group(1)
        if name == "befund":
            return finding.reason or ""
        try:
            return _short(table.get(name))
        except MissingSignal:
            return "[nicht erhoben]"

    text = _PLACEHOLDER.sub(substitute, template)

    leftover = _UNFINISHED.findall(text)
    if leftover:
        return "", (f"{finding.rule.id}: Erlaeuterungstext nicht verwendet, "
                    f"er enthaelt {len(leftover)} nicht aufgeloeste "
                    f"Platzhalter ({', '.join(sorted(set(leftover))[:3])})")
    return text, None


def _summary(findings: list) -> list:
    counts = {}
    for f in findings:
        counts[f.level] = counts.get(f.level, 0) + 1
    order = [CLEAR, SUSPECTED, UNRESOLVED, "unauffaellig", "nicht_anwendbar"]
    return [{"stufe": LEVEL_LABEL[level], "code": level, "anzahl": counts[level]}
            for level in order if counts.get(level)]


def _key_figures(run: Run, findings: list, eintraege: list) -> list:
    """The four numbers across the top of the document.

    "Geprüfte Schritte" is written as "3 von 4" only when the target
    profile says how many steps were planned. Without a profile there is
    no denominator, and inventing one would misstate what was skipped.
    """
    planned = run.target_profile.get("path") or run.target_profile.get("pfad")
    steps = f"{len(run.steps)}"
    if isinstance(planned, list) and len(planned) >= len(run.steps):
        steps = f"{len(run.steps)} von {len(planned)}"

    images = {b["datei"] for e in eintraege for b in e["screenshots"]
              if b["vorhanden"]}
    clear = sum(1 for f in findings if f.level == CLEAR)
    return [("Geprüfte Schritte", steps),
            ("Befunde", str(len(eintraege))),
            ("Nachweise", f"{len(images)} Dateien"),
            ("Eindeutig", str(clear))]


def _all_evidence(eintraege: list) -> list:
    """Every screenshot once, for the full-size appendix.

    The detail blocks show thumbnails; a thumbnail does not prove
    anything you cannot read. The appendix carries the readable image,
    and both point at the same file name and hash.
    """
    seen, images = set(), []
    for entry in eintraege:
        for image in entry["screenshots"]:
            if image["datei"] in seen:
                continue
            seen.add(image["datei"])
            images.append({**image, "befund": entry["regel"].id})
    return images


def _screenshot_names(findings: list, run: Run) -> set:
    names = {s.get("screenshot") for s in run.steps
             if isinstance(s, dict) and s.get("screenshot")}
    for f in findings:
        names.update(e.get("evidence") for e in f.evidence)
    return {n for n in names if isinstance(n, str) and n.lower().endswith(".png")}


def _short(value) -> str:
    if isinstance(value, bool):
        return "ja" if value else "nein"
    return str(value)


def _environment() -> Environment:
    environment = Environment(
        loader=FileSystemLoader(Path(__file__).parent / "templates"),
        autoescape=select_autoescape(["html"]), trim_blocks=True,
        lstrip_blocks=True, undefined=ChainableUndefined)
    environment.filters["absatz"] = lambda t: [
        p.strip() for p in (t or "").split("\n\n") if p.strip()]
    # The shared stylesheet is included as a template, so the embedded
    # fonts are available to all three views through one environment.
    environment.globals["fonts"] = fonts
    return environment
