"""What happens when the capture layer delivers something other than agreed?

From Tuesday no developer is available. A crash is then unfixable — a
partial output with an understandable note is not. So every deviation from
the contract has to lead to a result, not a stack trace.
"""

import json, sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.run import load_run
from dpm.engine.rules import load_rules
from dpm.engine.verdict import assess
from dpm.report.case_file import build

RULES = load_rules()
HEALTHY = json.loads(pathlib.Path("data/fixtures/viagogo/capture.json").read_text())


def run_with(mutation, name):
    raw = json.loads(json.dumps(HEALTHY))
    mutation(raw)
    with tempfile.TemporaryDirectory() as tmp:
        folder = pathlib.Path(tmp)
        (folder / "capture.json").write_text(json.dumps(raw), encoding="utf-8")
        run = load_run(folder)
        findings = [assess(r, run.table) for r in RULES]
        case = build(run, findings, output=folder / "out", as_pdf=False)
        assert case.html.exists(), f"{name}: no case file produced"
        return run, findings, case.html.read_text(encoding="utf-8")


cases = [
    ("bare signal value instead of {value, step, evidence}",
     lambda r: r["signals"].update({"banner_detected": True})),
    ("signal value null",
     lambda r: r["signals"].update({"banner_detected": {"value": None, "step": "x"}})),
    ("no viewport in meta",
     lambda r: r["meta"].pop("viewport")),
    ("no timestamp, no run_id",
     lambda r: [r["meta"].pop("timestamp"), r["meta"].pop("run_id")]),
    ("empty signal list",
     lambda r: r.update({"signals": {}})),
    ("no steps",
     lambda r: r.update({"steps": []})),
    ("step without a name",
     lambda r: r["steps"].append({"url": "x"})),
    ("step is a string",
     lambda r: r["steps"].append("startseite")),
    ("signal refers to an unknown step",
     lambda r: r["signals"]["banner_detected"].update({"step": "does-not-exist"})),
    ("target name with a path change",
     lambda r: r["meta"].update({"target": "../../rules/DP-001_Consent-Buttons"})),
    ("run_id with a slash",
     lambda r: r["meta"].update({"run_id": "../outside/run"})),
    ("signal_errors missing entirely",
     lambda r: r.pop("signal_errors")),
    ("legacy German key names",
     lambda r: r.update({"schritte": r.pop("steps")})),
]

for name, mutation in cases:
    run_with(mutation, name)
    print(f"  ok  {name}")

print("\nThe file never asserts a screenshot that does not exist")
with tempfile.TemporaryDirectory() as tmp:
    folder = pathlib.Path(tmp)
    (folder / "capture.json").write_text(json.dumps(HEALTHY), encoding="utf-8")
    run = load_run(folder)                       # without the PNG files next to it
    findings = [assess(r, run.table) for r in RULES]
    case = build(run, findings, output=folder / "out", as_pdf=False)
    html = case.html.read_text(encoding="utf-8")
    assert "<img" not in html, "case file links an image that does not exist"
    assert "nicht bei" in html
print("  ok  a missing screenshot is declared, not linked")

print("\nEscaping the output folder")
run, _, _ = run_with(lambda r: r["meta"].update({"run_id": "../outside/run"}), "run_id")
assert "/" not in run.run_id and not run.run_id.startswith("."), run.run_id
assert (pathlib.Path("out") / run.run_id).resolve().parent == pathlib.Path("out").resolve()
print(f"  ok  run_id defused to {run.run_id!r}")
run, _, _ = run_with(lambda r: r["meta"].update({"target": "../../rules/DP-001_Consent-Buttons"}),
                     "target")
assert run.target_profile == {}, "a foreign file was loaded as a target profile"
print("  ok  a target name with a path change loads no foreign profile")

print("\nLegacy German keys are still readable, but reported")
run, _, _ = run_with(lambda r: r.update({"schritte": r.pop("steps")}), "legacy")
assert run.steps, "German 'schritte' no longer read"
assert any("German key names" in w for w in run.warnings), run.warnings
print("  ok  old schema still runs and says so")

print("\nWarnings reach the document")
run, _, html = run_with(lambda r: r["signals"].update({"banner_detected": True}),
                        "bare value")
assert any("without provenance" in w for w in run.warnings), run.warnings
assert "without provenance" in html
print("  ok  a contract violation appears in the file, not only in the terminal")

print("\nAll robustness tests passed.")
