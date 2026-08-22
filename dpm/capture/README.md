# Capture layer

Walks a target and writes `out/<run_id>/capture.json` — the only thing the
evaluation layer ever reads. Schema: [`data/fixtures/README.md`](../../data/fixtures/README.md).

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium

export GEMINI_API_KEY=…                    # free tier, ~10–15 requests/minute
.venv/bin/python -m dpm capture viagogo    # profile from data/targets/viagogo.yaml
.venv/bin/python -m dpm assess out/<run_id>
```

Without a key it still runs: the start page, its screenshot and its hash are
captured, and every signal lands in `signal_errors`. That is a valid partial
capture, not a failure.

## Where the model comes from

One environment variable decides the backend; nothing in the code changes.

```bash
GEMINI_API_KEY=…                                    # AI Studio, free tier
DPM_VERTEX=1 GOOGLE_CLOUD_PROJECT=… gcloud auth application-default login
```

Use Vertex if the hackathon credits should pay for it: the 300 USD Google
Cloud credit explicitly excludes *Gemini API in AI Studio* and covers Vertex
AI. Cost is not the reason — five to eleven calls per run is about one cent
— the free tier's rate limit on presentation day is.

| Variable | Default | |
|---|---|---|
| `DPM_MODEL` | `gemini-2.5-flash-lite` | cheapest vision tier; the two tasks need no reasoning |
| `DPM_MIN_CONFIDENCE` | `0.7` | below this a read signal becomes a `signal_error` |
| `GOOGLE_CLOUD_LOCATION` | `europe-west4` | Vertex only |

## Files

| | |
|---|---|
| `driver.py` | browser boot, the step loop, writes `capture.json` |
| `path.py` | the five path step names |
| `targets.py` | reads `data/targets/<name>.yaml` |
| `som_overlay.js` | numbered boxes for the navigator — pure browser JS |
| `../ai/client.py` | the one place a model is called from |
| `../ai/navigator.py` | AI ③ — which box leads further |
| `../ai/text_signals.py` | AI ① — what a screenshot honestly shows |

## Still missing

Ordered by what blocks a finding. Ownership: capture layer.

1. **`dpm/signals/extractors.js`** — deterministic measurement in the browser.
   Without it DP-001 and DP-002, the two finished rules, can only be `unklar`:
   `banner_detected`, `accept_button_area_px2`, `reject_button_area_px2`, both
   contrast ratios, `reject_button_present`, `preselected_checkbox_count`,
   `third_party_cookies_before_consent`. All of it is
   `getBoundingClientRect()` and `getComputedStyle()`, roughly 100 lines. A
   model cannot read a px² area or a WCAG contrast ratio off an image, and
   reproducibility is our whole claim against the ML approach.
2. **Path execution in `path.py`** — the six verbs `navigate` · `search` ·
   `click` · `click_first_result` · `scroll` · `wait`, driven from
   `data/targets/*.yaml`. The navigator can only click, so on a site that
   needs a search it never reaches `produktdetail` — where the scarcity note
   and the VAT line live. `data/targets/viagogo.yaml` already declares the
   path.
3. **`reject_click_depth`** — how many interactions until consent is fully
   refused. Deliberately absent: the ported code counted funnel clicks under
   that name, and DP-001 judges on it, so it produced a confident wrong
   finding. Better no signal than a wrong one.
4. **Second capture of the same target** — clean browser state, revisit, same
   start value. DP-003 needs `countdown_unchanged_scans` and
   `scarcity_value_unchanged_scans`, so without it our strongest rule cannot
   fire either.

## Two rules this layer must not break

**A measurement that failed is never `null`, `0`, `false` or `-1`.** `false`
means *measured, and it is not there*. `signal_errors` means *we could not
check*. Those are different legal statements, and the engine turns the second
into `unklar` on its own — but only while they stay apart. `scarcity_value`
on "nur noch wenige verfügbar" has no number and belongs in `signal_errors`.

**A step that fails does not lose the steps before it.** `capture()` never
raises; whatever was reached is written. A partial capture is still evidence
and is exactly how `unklar` should arise.
