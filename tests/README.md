# Tests

Runnable without setup, no external services:

```
.venv/bin/python tests/test_conditions.py     # condition parser
.venv/bin/python tests/test_verdicts.py       # rulebook against the fixture
.venv/bin/python tests/test_case_file.py      # Beweisakte
.venv/bin/python tests/test_false_alarms.py   # can the system stay silent?
.venv/bin/python tests/test_robustness.py     # broken capture.json — result, not crash
```

`tests/test_verdicts.py` checks the hand-written fixture
`data/fixtures/viagogo/` against the real rulebook. If a verdict moves, the
test breaks — then please look at it rather than quietly adjusting the
expected value.
