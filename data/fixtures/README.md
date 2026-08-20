# Fixtures — hand-written capture runs

No real measurements. Purpose: build and check the evaluation layer
(rulebook, Beweisakte, market overview) **without waiting for the capture
layer** — and afterwards serve as a regression test.

| Folder | What it represents | Expected result |
|---|---|---|
| `viagogo/` | reference case, named by the consumer agency | 3 × eindeutig, 3 × unklar |
| `sauberer-shop/` | unremarkable shop, correctly designed | no finding |
| `ratgeber-portal/` | editorial portal, no shop, no banner | rules do not apply at all |

**`sauberer-shop` and `ratgeber-portal` deliberately have no target profile
in `data/targets/`.** That verifies an arbitrary target runs through the
whole chain without hand setup — the tool is meant for any website, not
only the ones we prepared.

The consequence is visible and intended: without human confirmation in the
target profile (`confirmed_by_human`), a rule whose applicability rests on
a derivation is capped at `verdaechtig` (C4).

## Schema

English keys throughout:

```jsonc
{
  "meta":   { "target", "industry", "start_url", "timestamp", "capture_mode",
              "viewport", "locale", "timezone", "user_agent", "run_id" },
  "steps":  [ { "step", "url", "screenshot", "dom_hash" } ],
  "signals": { "<name>": { "value", "step", "evidence" } },
  "signal_errors": { "<name>": "why it could not be measured" }
}
```

The older German spellings (`schritte`, `wert`, `nachweis`, `ziel`,
`branche`) are still read, but produce a warning.

If a result changes, `tests/test_verdicts.py` or
`tests/test_false_alarms.py` breaks. Then look at it — do not silently
adjust the expected value.
