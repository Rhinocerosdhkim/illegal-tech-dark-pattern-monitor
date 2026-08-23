"""The Beweisakte is the document that accompanies a warning letter. A
factual error in it is more expensive than a crash. So the focus here is:
does it contain only what was actually measured?
"""

import shutil, sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.run import load_run
from dpm.engine.rules import load_rules
from dpm.engine.verdict import assess
from dpm.report.case_file import _evidence, build, step_index

run = load_run("data/fixtures/viagogo")
findings = [assess(r, run.table) for r in load_rules()]

with tempfile.TemporaryDirectory() as tmp:
    case = build(run, findings, output=tmp, as_pdf=False)
    html = case.html.read_text(encoding="utf-8")

    # DP-004 greift auf einem Ticketverkauf nicht (kein Dauerschuldverhaeltnis)
    # und erscheint deshalb gar nicht in der Akte.
    assert case.finding_count == 5, case.finding_count
    print("  ok  5 reportable findings, DP-004 correctly absent")

    # The decisive test: no measured value may be shown as "not captured".
    # That would be a false statement of fact.
    measured = {"accept_button_area_px2", "reject_click_depth",
                "preselected_checkbox_count", "third_party_cookies_before_consent"}
    assert measured <= set(run.table.values), "fixture changed?"
    assert "[nicht erhoben]" not in html, \
        "a measured value is shown as not captured"
    print("  ok  no measured value shown as 'nicht erhoben'")

    for needle, name in [
            ("sha256:", "DOM hash"),
            ("Erfassungsbedingungen", "reproducibility"),
            ("Herkunft der Schwellenwerte", "threshold_source"),
            # Spelling follows the design handoff ("Bekannte Fehlalarm-Risiken"),
            # which supplies the final German copy for every label.
            ("Fehlalarm-Risiken", "false_positive_risks"),
            ("Anspruchskette", "claim chain"),
            ("PLATZHALTER", "provisional notice (packet 3 outstanding)"),
            ("Nicht erhoben", "measurement gaps are named"),
            ("S-01.png", "screenshot embedded")]:
        assert needle in html, f"missing from the case file: {name}"
        print(f"  ok  {name}")

    assert "Irrefuehrung" not in html, "category without umlaut in the document"
    print("  ok  categories in correct German spelling")

    for name in ("S-01.png", "S-03.png"):
        assert (case.html.parent / name).exists(), f"{name} not copied along"
    print("  ok  output folder is self-contained")

print("\nBuilt into the capture's own folder")
# A live capture writes out/<run_id>/ and the Beweisakte is built into the
# same folder. Before this was handled, "python -m dpm report out/<run_id>"
# died on copying a screenshot onto itself.
with tempfile.TemporaryDirectory() as tmp:
    folder = pathlib.Path(tmp) / run.run_id
    shutil.copytree("data/fixtures/viagogo", folder)
    same = load_run(folder)
    result = build(same, [assess(rule, same.table) for rule in load_rules()],
                   output=tmp, as_pdf=False)
    assert result.html.exists()
    assert (folder / "S-01.png").exists(), "the evidence was lost"
    print("  ok  no SameFileError, screenshots still there")

print("\nThe hash under a screenshot belongs to that screenshot")
# A walk can pass the same page twice, and since a signal keeps the step it
# was really measured on, its evidence may point at the earlier of two steps
# with the same name. Keyed by name alone, the Beweisakte printed the hash
# of the LAST such step under the image of the first — and that hash is what
# proves the image shows that page state.
import json

with tempfile.TemporaryDirectory() as tmp:
    folder = pathlib.Path(tmp) / "doppelt"
    folder.mkdir()
    (folder / "capture.json").write_text(json.dumps({
        "meta": {"target": "doppelt", "industry": "Test",
                 "run_id": "2026-08-22T00-00-00_doppelt"},
        "steps": [
            {"step": "startseite", "url": "https://a.de/",
             "screenshot": "S-01.png", "dom_hash": "sha256:aaaa"},
            {"step": "startseite", "url": "https://a.de/nach-consent",
             "screenshot": "S-02.png", "dom_hash": "sha256:bbbb"},
        ],
        "signals": {
            "banner_detected": {"value": True, "step": "startseite",
                                "evidence": "S-01.png"},
            "preselected_checkbox_count": {"value": 2, "step": "startseite",
                                           "evidence": "S-01.png"},
        },
        "signal_errors": {},
    }, ensure_ascii=False), encoding="utf-8")

    doubled = load_run(folder)
    case = build(doubled, [assess(r, doubled.table) for r in load_rules()],
                 output=folder / "out", as_pdf=False)
    # Checked on the data rather than on the rendered page: the evidence
    # rows and the Erfassungsprotokoll both print hashes, and a search over
    # the text cannot tell which one it found.
    index = step_index(doubled)
    for finding in [assess(r, doubled.table) for r in load_rules()]:
        for raw in finding.evidence:
            shown = _evidence(raw, index)
            assert shown["dom_hash"] == "sha256:aaaa", \
                f"{raw['signal']} auf {raw['evidence']}: {shown['dom_hash']}"
            assert shown["url"] == "https://a.de/", shown["url"]
    assert case.html.exists()
    print("  ok  Hash und Adresse gehoeren zum Screenshot des Signals")

print("\nAn explanation may never claim more than its level does")

from dpm.report.case_file import INCOMPLETE_TEXT, _explanation
from dpm.engine.verdict import UNRESOLVED


class _Rule:
    def __init__(self, templates):
        self.id, self.name, self.explanation_template = "DP-XXX", "Probe", templates


class _Finding:
    def __init__(self, level, templates):
        self.level, self.rule = level, _Rule(templates)
        self.reason, self.notes, self.evidence, self.unresolved = "", [], [], []


table = load_run("data/fixtures/viagogo").table

# "unklar" means a value could not be measured, so it asserts nothing. A
# text written for the rule in general describes a measurement, and printing
# it here claims more than the finding does -- DP-005 put its checkout-price
# paragraph directly under "Nicht erhoben, deshalb keine Feststellung".
text, problem = _explanation(_Finding(UNRESOLVED, {"*": "Festgestellt wurde X."}), table)
assert text == "" and problem is None, (text, problem)
print("  ok  a '*' text is not used at unklar")

# A rule that wants to speak at unklar says so explicitly, as DP-006 does.
text, _ = _explanation(
    _Finding(UNRESOLVED, {"*": "Festgestellt wurde X.", "unklar": "Nicht messbar."}),
    table)
assert text == "Nicht messbar.", text
print("  ok  an explicit unklar text is still used")

text, _ = _explanation(_Finding("verdaechtig", {"*": "Allgemeiner Text."}), table)
assert text == "Allgemeiner Text.", text
print("  ok  and '*' still serves the levels that do assert something")

# Placeholders the legal team left behind went into the PDF verbatim:
# [CHECKOUT_PRICE], and the conditional form the rulebook proposes but no
# engine implements. Better an openly named gap than a printed marker.
for template, what in [("Preis war [CHECKOUT_PRICE] am Ende.", "[CHECKOUT_PRICE]"),
                       ("Es {countdown_personalized == false, default: 'x'} so.",
                        "the conditional form")]:
    text, problem = _explanation(_Finding("verdaechtig", {"*": template}), table)
    assert text == "", f"{what} reached the document: {text!r}"
    assert problem and "DP-XXX" in problem, problem
    print(f"  ok  {what} is dropped and reported")

# A real measurement must still substitute.
text, problem = _explanation(
    _Finding("verdaechtig", {"*": "Gemessen: {reject_click_depth}."}), table)
assert text == "Gemessen: 3." and problem is None, (text, problem)
print("  ok  a real signal still substitutes")

# And the whole way through: nothing unresolved reaches the rendered file,
# the reader is told why, and the command can say so too.
with tempfile.TemporaryDirectory() as tmp:
    result = build(run, findings, output=tmp, as_pdf=False)
    page = result.html.read_text(encoding="utf-8")
    import re as _re
    left = [m for m in _re.findall(r"\[[A-Z][A-Z0-9_]{2,}\]", page)]
    assert not left, f"placeholders still in the document: {left}"
    assert INCOMPLETE_TEXT[:40] in page, "the reader is not told the text is missing"
    assert result.warnings, "the command would have stayed silent about it"
    print(f"  ok  0 placeholders in the file, {len(result.warnings)} warnings raised")


print("\nAll case-file tests passed.")
