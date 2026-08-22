# Tests

Runnable without setup, no external services:

```
.venv/bin/python tests/test_capture.py        # capture layer, no network
.venv/bin/python tests/test_conditions.py     # condition parser
.venv/bin/python tests/test_verdicts.py       # rulebook against the fixture
.venv/bin/python tests/test_case_file.py      # Beweisakte
.venv/bin/python tests/test_false_alarms.py   # can the system stay silent?
.venv/bin/python tests/test_robustness.py     # broken capture.json — result, not crash
.venv/bin/python tests/test_rule_defects.py   # guards for the rulebook repairs of 20.08.
.venv/bin/python tests/test_overview.py       # Marktübersicht: aggregation, filters, CSV
.venv/bin/python tests/test_timeline.py       # Zeitachse: two captures compared
.venv/bin/python tests/test_pdf_export.py     # PDF export with the filter applied
.venv/bin/python tests/test_rebuild.py        # the handover command, run discovery
.venv/bin/python tests/test_design.py         # greyscale proof, nothing fetched
.venv/bin/python tests/test_gold.py           # accuracy figures and their denominators
.venv/bin/python tests/test_ai_guards.py      # what AI 2 and AI 4 may put in a document
```

`tests/test_verdicts.py` checks the hand-written fixture
`data/fixtures/viagogo/` against the real rulebook. If a verdict moves, the
test breaks — then please look at it rather than quietly adjusting the
expected value.
