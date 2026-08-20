"""The Beweisakte is the document that accompanies a warning letter. A
factual error in it is more expensive than a crash. So the focus here is:
does it contain only what was actually measured?
"""

import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.run import load_run
from dpm.engine.rules import load_rules
from dpm.engine.verdict import assess
from dpm.report.case_file import build

run = load_run("data/fixtures/viagogo")
findings = [assess(r, run.table) for r in load_rules()]

with tempfile.TemporaryDirectory() as tmp:
    case = build(run, findings, output=tmp, as_pdf=False)
    html = case.html.read_text(encoding="utf-8")

    assert case.finding_count == 6, case.finding_count
    print("  ok  6 reportable findings")

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
            ("Fehlalarmrisiken", "false_positive_risks"),
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

print("\nAll case-file tests passed.")
