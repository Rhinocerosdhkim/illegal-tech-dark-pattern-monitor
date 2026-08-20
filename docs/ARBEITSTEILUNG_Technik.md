# Division of Labour — Capture vs. Engine

**Donghyun + Karthik** · companion to [`AGENDA_Technik.md`](AGENDA_Technik.md)
Read this before we next talk. Section 8 is the list of things I need an answer on from you.

> **This document supersedes [`PRODUKT_Architektur.md`](PRODUKT_Architektur.md) §7** for the directory layout. That section was written assuming Node; the layout below is the Python one. Everything else in `PRODUKT_Architektur.md` (the pipeline, where AI sits, the three views) still stands unchanged.

---

## 0. Three premises that changed

**1. We go Python.**

The only real argument for Node was that `extractors.js` could be reused unchanged as a Chrome extension content script. **We can keep that anyway** — and we should:

> Signal measurement lives in **`dpm/signals/extractors.js`, a real `.js` file with no Python in it.**
> Python reads that file and injects it via `page.evaluate()`.

Do **not** embed measurement JS as Python string literals. If it is a separate file, we keep editor support, we keep the extension option alive at the cost of a manifest and a popup, and the measurement code stays honest about where it actually runs. This is a hard requirement on your side, not a preference.

**2. Our availability is not symmetric.** I am out from Tuesday. You are available through Thursday. This is what actually drives the split below — see section 1.

**3. Rules are coming.** Paul is delivering DP-001, DP-002 and DP-003 (the countdown pattern — our strongest one). The open schema questions from [`ABSTIMMUNG_Regelwerk.md`](ABSTIMMUNG_Regelwerk.md) are being settled and the rule files will be normalised accordingly. **Neither of us waits for any of this.** I build the engine against the recommended forms (`all:`/`any:`/`none:`, object-form `condition` + `reason` without `severity`, `menschliche_pruefung`); you never touch rule files at all.

---

## 1. The principle: the layer that rots vs. the layer that freezes

| | Nature | Owner |
|---|---|---|
| **Capture** | **Rots.** viagogo changes its markup, bot detection appears, selectors break. May need fixing right up to presentation day | **Karthik** — available through Thursday |
| **Engine · Report · UI** | **Does not rot.** Deterministic over a stored `capture.json`. Once correct, stays correct | **Donghyun** — frozen Monday |

The existing split maps exactly onto our availability. That is convenient, but it has one consequence that is **the most important line in this document**:

> **On Tuesday and Wednesday you must be able to re-capture a site and regenerate every output without me and without touching my code.**

So the thing I owe you is not a feature, it is a contract — section 4.

---

## 2. Karthik — capture layer

```
dpm/capture/     driver.py · path.py · targets.py
dpm/signals/     extractors.js (pure browser JS) · collect.py
dpm/ai/          client.py · text_signals.py · navigator.py
data/targets/    <name>.yaml
```

> **Layout changed from `src/` to `dpm/`.** A `src/` layout needs
> `pip install -e .`; that is one more step on the Monday handover, which is
> the one failure mode we named. From the repo root, `python -m dpm` works
> with no install at all. Your directories are `dpm/capture/` and
> `dpm/signals/`.

**Schema is English.** `capture.json` and `data/targets/*.yaml` use
`steps` / `step` / `value` / `evidence` / `target` / `industry` / `path` /
`action` / `selector` / `confirmed_by_human`. The older German spellings are
still read, but produce a warning. See `data/fixtures/README.md`.

| | Task | Done means |
|---|---|---|
| 1 | Playwright (Python, sync API) boot | `viewport`, `locale=de-DE`, `timezone=Europe/Berlin`, `user_agent` **fixed in code**. Nothing left to defaults — pixel areas are meaningless without a fixed viewport, and reproducibility is our whole claim against the ML approach |
| 2 | Path execution, six verbs: `navigate` · `suche` · `klick` · `klick_erstes_ergebnis` · `scroll` · `warte` | **Every selector lives in `data/targets/*.yaml`. Zero selectors in Python.** When viagogo changes its markup, you edit YAML, not code — that is what makes Tue/Wed maintenance possible |
| 3 | Per-step screenshot, `dom_hash`, timestamp | Hash is computed on a **normalised** DOM (strip nonces, ad IDs, timestamps). Otherwise every capture differs and the timeline diff is worthless |
| 4 | `extractors.js` — the measurements | **No Python in this file.** Injected via `page.evaluate()`. Would run unchanged as a content script |
| 5 | Write `capture.json` | Every signal is `{ value, step, evidence }`. Never a bare value — see the box below |
| 6 | Partial capture on failure | Step 3 dies → steps 1–2 are kept, the rest goes to `signal_errors` **with the step name and a reason**. A partial capture is still useful, and it is exactly how `unklar` should arise |
| 7 | Countdown proof: two captures | Clean browser state, revisit, same start value. This is the single most convincing thing in the demo |
| 8 | **AI ① — wording interpretation** + the shared LLM wrapper `ai/client.py` | Output is **value + confidence**. Below the threshold the signal goes to `signal_errors`, not into `signals` |
| 9 | **AI ③ — path navigation** (only once capture is stable) | The chosen element **and the reason** are recorded in `capture.json`. If a human cannot audit the path afterwards, it is not usable for us |
| 10 | Two backup sites in the same industry | In case viagogo blocks us |

> ### ⚠️ The one mistake that would quietly corrupt everything
> A measurement that failed is **never** written as `null`, `0`, `false` or `-1`.
> `false` means *"measured, and it is not there."* `signal_errors` means *"we could not check."*
> Those are two completely different legal statements. My engine turns the second into `unklar` automatically — but only if you keep them apart.

**You write the shared LLM wrapper** (`ai/client.py`) because AI ① is needed before anything of mine is. I will reuse it for ② and ④. Two separate LLM clients would be waste.

**What you do Tue/Wed without me:** fix selectors, re-capture, add targets, adjust paths. **All of it inside `capture/`, `signals/` and `targets/`.**

---

## 3. Donghyun — engine, report, UI

```
dpm/engine/      rules.py · conditions.py · verdict.py · run.py · derivations.py
dpm/report/      case_file.py · overview.py · diff.py · templates/
dpm/ui/          app.py
dpm/ai/          doc_import.py · narrative.py
```

| | Task | Needs a rule file? |
|---|---|---|
| 1 | YAML loader + condition parser (`> < >= <= == != and`), **no `eval()`** — a small parser of our own | no |
| 2 | `all:` / `any:` / `none:` and object-form `condition` + `reason` | no |
| 3 | **`signal_errors` → automatic `unklar`** | no |
| 4 | Applicability derived from fact signals caps the rule at `verdächtig` | no |
| 5 | Evidence binding: finding → step → screenshot → hash → timestamp | no |
| 6 | Beweisakte: Jinja2 → HTML → PDF via Playwright `page.pdf()` | DP-001 only |
| 7 | `menschliche_pruefung` printed as a checklist under each finding | no |
| 8 | Marktübersicht: filters, statistics, CSV export | no |
| 9 | Timeline diff between two `capture.json` files | no |
| 10 | UI, three views, reference mode vs. live mode | no |
| 11 | **AI ② document import · AI ④ report prose** | no |
| 12 | **The handover contract** — section 4 | no |

Eleven of twelve need no rule file, so I am not blocked by the rulebook and you are never blocked by me.

---

## 4. What I owe you for Tuesday and Wednesday

```bash
python -m dpm report <run_id>     # stored capture.json → Beweisakte + Marktübersicht, regenerated
```

No engine edits, no capture code touched, no environment variables, no keys, no setup. You re-capture viagogo on Wednesday, run one command, and the presentation material is current.

Same reason the UI stays **one rendering path — Jinja2 + FastAPI**. Adding Streamlit would give us a second, parallel way of rendering the same data, and it cannot produce the Beweisakte PDF anyway. One set of templates feeds the screen, the PDF and the CSV.

If this command does not exist on Monday, the product dies the moment I leave. It is my responsibility, listed here so you can hold me to it.

---

## 5. Boundaries neither of us crosses

| Rule | Why |
|---|---|
| You do not touch `engine/`, `report/`, `ui/` | What I froze Monday must stay frozen, or the accuracy numbers we quote are no longer about the thing we are showing |
| I do not touch `capture/`, `signals/`, `targets/` | The selector knowledge is yours |
| **Neither of us changes the `capture.json` schema alone** | It is the contract. Changing it means both of us agree and the fixture is updated in the same commit |
| **No model call anywhere outside `src/ai/`** | We have to be able to prove where we do *not* use AI. `engine/` containing no LLM import at all is both an architecture rule and our strongest slide |
| Rule files (`rules/*.yaml`) belong to the legal team | Neither of us edits them to make our code pass |

---

## 6. The one thing we do together, before splitting

**Hand-written fixtures: `data/fixtures/<target>/capture.json` plus a few screenshots.** Three exist already — `viagogo`, `sauberer-shop`, `ratgeber-portal`. They are the schema you have to produce; read one before you start.

- Fill it with exactly the signals DP-001 needs, and put **one entry in `signal_errors` on purpose** so the `unklar` path is exercised from day one.
- **I write it** — the consumer writes the contract, because I am the one who finds out at 2am what the engine actually needs.
- **You confirm you can produce that shape.** That is your whole involvement.

After this file exists, neither of us waits for the other for anything, and the fixture doubles as our regression test. Twenty minutes of work.

---

## 7. Python specifics

| | Choice | Note |
|---|---|---|
| Browser | `playwright` (sync API) | async buys us nothing here and costs debugging time |
| Rules | `PyYAML` | |
| Templates | `Jinja2` | one path for screen, PDF and CSV |
| PDF | Playwright `page.pdf()` on our own HTML | Playwright is already a dependency; no WeasyPrint, no wkhtmltopdf |
| UI | `FastAPI` + `uvicorn` | thin shell — three views, no accounts, no database |
| CSV | stdlib `csv` | |
| **Not used** | pandas, any database, any ORM | one capture run = one JSON file plus screenshots; the timeline is a comparison of two files |

Polite retrieval stays as agreed: public pages only, no login, no bypassing access controls, a visible delay between requests, never two targets in parallel. We will be asked about this in the Q&A.

---

## 8. What I need from you when you come back

- [ ] **Python confirmed?** If you are meaningfully faster in something else, say it now rather than later
- [ ] `extractors.js` as a separate pure-JS file, injected — agreed?
- [ ] `dom_hash`: what exactly do we normalise before hashing
- [ ] Delay between requests — number, please
- [ ] Confidence threshold for AI ①, below which the signal goes to `signal_errors`
- [ ] Which model, and does it run in the handover case without a key in the repo
- [ ] Do you take AI ③ (navigation), or do we stay on hand-written target files and list ③ as future work
- [ ] Name of the single entry-point command *(open since [`AGENDA_Technik.md`](AGENDA_Technik.md) §8)*

Answers go into [`DECISIONS.md`](DECISIONS.md), not into a chat window. Decisions that only exist in a chat get re-discussed two days later.
