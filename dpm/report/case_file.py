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
from dataclasses import dataclass
from pathlib import Path

from jinja2 import (ChainableUndefined, Environment, FileSystemLoader,
                    select_autoescape)

from dpm import PRODUCT_NAME
from dpm.engine.conditions import MissingSignal, SignalTable
from dpm.engine.run import Run
from dpm.engine.rules import Rule
from dpm.engine.verdict import CLEAR, SUSPECTED, UNRESOLVED, Finding

LEVEL_LABEL = {CLEAR: "eindeutig", SUSPECTED: "verdächtig",
               UNRESOLVED: "unklar", "unauffaellig": "unauffällig",
               "nicht_anwendbar": "nicht anwendbar"}

_PLACEHOLDER = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

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


def build(run: Run, findings: list, output: str | Path = "out",
          as_pdf: bool = True) -> CaseFile:
    folder = Path(output) / run.run_id
    folder.mkdir(parents=True, exist_ok=True)

    reportable = [f for f in findings if f.reportable]
    steps = {s["step"]: s for s in run.steps
             if isinstance(s, dict) and s.get("step")}

    for name in _screenshot_names(reportable, run):
        source = run.screenshot(name)
        if source:
            shutil.copyfile(source, folder / name)

    html = _environment().get_template("beweisakte.html").render(
        produkt=PRODUCT_NAME,
        lauf=run,
        meta=run.meta,
        schritte=run.steps,
        hinweis=PROVISIONAL_NOTICE,
        zusammenfassung=_summary(findings),
        eintraege=[_entry(nr, f, steps, run, folder)
                   for nr, f in enumerate(reportable, start=1)],
        kategorie=CATEGORY_LABEL,
        warnungen=run.warnings,
    )

    target_html = folder / "beweisakte.html"
    target_html.write_text(html, encoding="utf-8")

    pdf = _to_pdf(target_html) if as_pdf else None
    return CaseFile(html=target_html, pdf=pdf, finding_count=len(reportable))


# --- preparation ---------------------------------------------------------

def _entry(nr: int, finding: Finding, steps: dict, run: Run,
           folder: Path) -> dict:
    evidence = [_evidence(e, steps) for e in finding.evidence]
    return {
        "nr": nr,
        "regel": finding.rule,
        "stufe": LEVEL_LABEL[finding.level],
        "stufe_code": finding.level,
        "bedingung": finding.condition,
        "begruendung": finding.reason,
        "herabgestuft": finding.downgraded,
        "hinweise": finding.notes,
        "unklar_wegen": finding.unresolved,
        "wuerde_stufe": LEVEL_LABEL.get(finding.would_be_level or ""),
        "nachweise": evidence,
        "messwerte": ", ".join(f"{e['signal']} = {_short(e['value'])}"
                               for e in evidence) or "—",
        "screenshots": _images(evidence, folder),
        "erlaeuterung": _explanation(finding.rule, run.table),
    }


def _evidence(raw: dict, steps: dict) -> dict:
    label = raw.get("step")
    step = steps.get(label) or {}
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


def _explanation(rule: Rule, table: SignalTable) -> str:
    """Substitute {signal_name} with the measured value.

    The whole signal table is queried, not just the signals of the matching
    condition: the explanatory text regularly names measurements that
    merely put the finding in context.

    "[nicht erhoben]" appears only where nothing was actually measured. In
    a document that accompanies a warning letter, claiming something was
    not captured when it was would be a factual error.
    """
    if not rule.explanation_template:
        return ""

    def substitute(match):
        try:
            return _short(table.get(match.group(1)))
        except MissingSignal:
            return "[nicht erhoben]"

    return _PLACEHOLDER.sub(substitute, rule.explanation_template)


def _summary(findings: list) -> list:
    counts = {}
    for f in findings:
        counts[f.level] = counts.get(f.level, 0) + 1
    order = [CLEAR, SUSPECTED, UNRESOLVED, "unauffaellig", "nicht_anwendbar"]
    return [{"stufe": LEVEL_LABEL[level], "code": level, "anzahl": counts[level]}
            for level in order if counts.get(level)]


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
    return environment


# --- PDF -----------------------------------------------------------------

def _to_pdf(html: Path) -> Path | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    target = html.with_suffix(".pdf")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html.resolve().as_uri())
        page.pdf(path=str(target), format="A4", print_background=True,
                 margin={"top": "18mm", "bottom": "18mm",
                         "left": "16mm", "right": "16mm"})
        browser.close()
    return target
