# Signal measurement

```
extractors.js   the measurements — pure browser JS, no Python in it
collect.py      injects it and stamps step and evidence onto the result
```

`extractors.js` contains no Playwright and no imports. It is injected with
`page.evaluate()` and would run unchanged as a Chrome extension content
script — that is why it is a file and not a string literal in Python
([`ARBEITSTEILUNG_Technik.md`](../../docs/ARBEITSTEILUNG_Technik.md) §2, task 4).

## Wiring it into a capture

One line in `dpm/capture/driver.py`, in `_walk`, after the screenshot for
the step has been taken:

```python
from dpm.signals import collect
...
await collect.into(run, page, step=entry["step"], evidence=name)
```

Call it **after** `_read_signals`. Where a signal can come from both, the
measured value should win: a number read out of the DOM is deterministic
and anybody can recompute it in the developer tools; one read off a
screenshot by a model cannot be checked that way.

## What it measures, and what it deliberately does not

Only DOM signals — everything that is decided by the element tree, its
geometry and its computed styles, without clicking anything and without
the network.

| Group | Signals |
|---|---|
| Consent banner | `banner_detected` · `accept_button_area_px2` · `reject_button_area_px2` · `accept_contrast_ratio` · `reject_contrast_ratio` · `reject_button_present` · `preselected_checkbox_count` · `more_info_present` |
| Buttons | `order_button_found` · `order_button_label` · `has_kuendigungsbutton` · `kuendigungsbutton_label` · `kuendigungsbutton_font_size_px` · `kuendigungsbutton_contrast_ratio` · `kuendigungsbutton_hidden_in_menu` |
| Concealment | `required_info_found` · `required_info_type` · `font_size_min_px` · `text_contrast_min` · `hidden_by_opacity_count` · `scroll_depth_of_required_info_pct` |
| Prices, context | `has_price_display` · `has_checkout_flow` · `gratis_claim_present` · `vat_disclosure_present` · `vat_disclosure_scroll_pct` · `is_financial_services` · `page_language` |
| Contract type | `recurring_price_notation_present` · `recurring_price_period` · `min_contract_term_stated` · `auto_renewal_text_present` · `cancellation_terms_present` · `has_recurring_contract_keywords` |

**Not in here, and not by oversight:**

- `reject_click_depth`, `banner_reappears_on_reject` — these are procedures,
  not measurements. Somebody has to click, and that belongs in the driver.
- `third_party_cookies_before_consent` — not in the DOM at all. It sits in
  the browser's cookie jar and is read on the Playwright side.
- `countdown_*`, `scarcity_value`, `viewer_count_present` — read off the
  screenshot by AI ①. A countdown is a number that changes while you look
  at it; the DOM says nothing useful about whether it is honest.

## The rule this file exists to obey

> A measurement that failed is **never** written as `null`, `0` or `false`.

`false` means *measured, and it is not there*. An entry in `errors` means
*we could not check*. Those are two different statements about a company,
and the engine turns the second into `unklar` on its own — but only as
long as they are kept apart.

The sharpest case is a banner with no reject button. `reject_button_area_px2
= 0` would read as "measured, zero pixels" and make every area-ratio rule
fire; the finding would then be an artefact of our own measurement. So the
signal goes to `errors` with the reason, and `reject_button_present = false`
carries the fact — which is what DP-001 calls `eindeutig` anyway.

## Checking it

```bash
.venv/bin/python tests/test_extractors.py
```

Four pages built with `set_content()`, no site visited: a banner designed
against the user, one without a reject button, a correctly built one, and
a page with no banner at all. Every asserted number can be recomputed by
hand from the markup in the test.
