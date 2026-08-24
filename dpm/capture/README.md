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

Without a key it still runs, and it measures. The start page, its screenshot
and its hash are captured, and `dpm/signals/extractors.js` reads every DOM
signal — on a shop with a consent banner that is 27 measured signals and 15
uncaptured, enough for DP-001, DP-002, DP-005 and DP-006 to produce a
finding. What needs a model is the navigation and the signals read off the
screenshot (countdown, scarcity, viewer count); those land in
`signal_errors`. A keyless run is a valid partial capture, not a failure.

## Two ways in, one capture.json

```bash
python -m dpm.capture.main https://www.amazon.de/ Elektronik   # der Hauptweg
python -m dpm capture viagogo                                  # ohne Schluessel
```

Both write `out/<run_id>/capture.json` in the same schema, and the
evaluation layer cannot tell them apart. What differs is how far they get.

| | walks | needs a key |
|---|---|---|
| `dpm.capture.main` → `agent.py` | the funnel: search, product, basket, until a login wall | yes |
| `dpm capture` → `driver.py` | the start page | no |

**The agent is the main path.** The patterns the consumer agency named —
the scarcity note, the VAT line, the countdown — are not on the start
page, and only the agent reaches them.

**The driver is kept anyway, and not out of sentimentality.** It measures
every DOM signal without a model at all: on amazon.de that is 27 signals
and a complete consent-banner measurement. If the free tier's rate limit
hits during the presentation, or a key is missing on somebody else's
laptop, that is the difference between a smaller demo and no demo. The
web UI picks automatically: a key runs the agent, no key runs the driver
and says so on screen.

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
| `DPM_MODEL` | `gemini-3.5-flash-lite` | cheapest vision tier; the two tasks need no reasoning |
| `DPM_MIN_CONFIDENCE` | `0.7` | below this a read signal becomes a `signal_error` |
| `GOOGLE_CLOUD_LOCATION` | `europe-west4` | Vertex only |

## Files

| | |
|---|---|
| `driver.py` | browser boot, the step loop, writes `capture.json` |
| `path.py` | the step names, and which measurement may replace which |
| `targets.py` | reads `data/targets/<name>.yaml` |
| `som_overlay.js` | numbered boxes for the navigator — pure browser JS |
| `../signals/extractors.js` | the DOM measurements — pure browser JS, no Playwright |
| `../signals/collect.py` | injects it and stamps step and evidence |
| `../ai/client.py` | the one place a model is called from |
| `../ai/navigator.py` | AI ③ — which box leads further |
| `../ai/text_signals.py` | AI ① — what a screenshot honestly shows |

`extractors.js` was written and wired on 22.08. — 35 signals, called from
`_walk` at `driver.py` in both the keyless and the model branch, checked by
`tests/test_extractors.py` against four pages the test builds itself. It
carries what the element tree, its geometry and its computed styles decide.
Details and the full signal list: [`../signals/README.md`](../signals/README.md).

## Still missing

Ordered by what blocks a finding. Ownership: capture layer.

1. **Path execution in `path.py`** — the six verbs `navigate` · `search` ·
   `click` · `click_first_result` · `scroll` · `wait`, driven from
   `data/targets/*.yaml`. The navigator can only click, so on a site that
   needs a search it never reaches `produktdetail` — where the scarcity note
   and the VAT line live. `data/targets/viagogo.yaml` already declares the
   path.
2. **`reject_click_depth`** and **`banner_reappears_on_reject`** — how many
   interactions until consent is fully refused, and whether the banner comes
   back afterwards. Both are procedures, not measurements: somebody has to
   click, so they cannot come out of `extractors.js`. `reject_click_depth` is
   deliberately absent rather than approximated — the ported code counted
   funnel clicks under that name, and DP-001 judges on it, so it produced a
   confident wrong finding. Better no signal than a wrong one.
3. **`third_party_cookies_before_consent`** — not in the DOM at all; it is in
   the browser's cookie jar and has to be read on the Playwright side, before
   any interaction with the banner. `_SIGNALE.md` calls it technically very
   reliable, and it is the one DP-001 condition that is independent of how the
   banner looks.
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
