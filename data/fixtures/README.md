# Fixtures — hand-written capture runs

No real measurements. Purpose: build and check the evaluation layer
(rulebook, Beweisakte, market overview) **without waiting for the capture
layer** — and afterwards serve as a regression test.

| Folder | What it represents | Expected result |
|---|---|---|
| `viagogo/` | reference case, named by the consumer agency | 4 × verdaechtig · 1 × unklar · 1 × nicht anwendbar |
| `viagogo-2026-09/` | the same site three weeks later | 2 × verdaechtig · 1 × unklar · 2 × unauffaellig · 1 × nicht anwendbar — for the timeline, see below |
| `sauberer-shop/` | unremarkable shop, correctly designed | 2 × unklar · 3 × unauffaellig · 1 × nicht anwendbar — **no verdaechtig, no eindeutig** |
| `ratgeber-portal/` | editorial portal, no shop, no banner | 6 × nicht anwendbar — the rules do not apply at all |
| `nachrichtenportal/` | news site, tracking before any banner | 1 × eindeutig · 5 × nicht anwendbar |

The numbers above are what the engine produces today; `tests/test_verdicts.py`
and `tests/test_false_alarms.py` assert exactly them. If you change a rule and
a number here stops matching, one of the two is wrong — look, do not adjust
silently.

`sauberer-shop` is the false-alarm test, so read its row carefully: the two
`unklar` are not findings. `unklar` asserts nothing — it says a signal could
not be measured, and here that is three the capture layer does not produce
yet: `banner_reappears_on_reject` and `banner_reappears_count_24h` for
DP-001, `preselected_paid_addon_count` for DP-005. Both rows become
`unauffaellig` once those signals exist.

`nachrichtenportal` is the only fixture that reaches `eindeutig`, and it does
so without a target profile: a banner that offers no way to refuse, the OLG
Köln 6 U 80/23 branch of DP-001. It is the case that justifies the top level
existing at all.

**Only `viagogo` has a target profile in `data/targets/`.** The other four
deliberately do not. That verifies an arbitrary target runs through the
whole chain without hand setup — the tool is meant for any website, not
only the ones we prepared.

The consequence is visible and intended: without human confirmation in the
target profile (`confirmed_by_human`), a rule whose applicability rests on
a derivation is capped at `verdaechtig` (C4).

## The second viagogo capture

`viagogo-2026-09/` exists so the Zeitachse has something to compare. Three
different kinds of change are represented on purpose:

| Rule | Change | Why it is in there |
|---|---|---|
| DP-003 | `verdaechtig` → `unauffaellig` | the countdown is gone — a finding was corrected |
| DP-002 | `verdaechtig` → `unauffaellig` | the button label was fixed |
| DP-001 | `verdaechtig` → `verdaechtig` | **the level is unchanged but the facts are not**: tracking before consent stopped, pre-ticked checkboxes appeared instead |

The third is the one a comparison of verdict levels alone would miss, and
the reason the timeline compares signals rather than verdicts.

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
