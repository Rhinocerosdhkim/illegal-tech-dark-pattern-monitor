# The four model call sites

A model is called from this directory and nowhere else. `engine/` contains
no model import at all, and that is deliberate: the evaluation of a
capture against the rulebook has to be reproducible by hand, and we have
to be able to say precisely which sentences a machine wrote.

| | Where | What it does | What it may not do |
|---|---|---|---|
| **AI ①** | `text_signals.py` | reads signals off a screenshot | write a value it is not sure of — below `DPM_MIN_CONFIDENCE` the signal goes to `signal_errors` |
| **AI ②** | `doc_import.py` | a document with links becomes a target list | name an address that is not in the document |
| **AI ③** | `navigator.py` | picks the next element on the path | act without recording which element and why |
| **AI ④** | `narrative.py` | formulates the German paragraph under a finding | name a value we did not measure, or assert a violation |

Nothing here decides a verdict. Levels come from `rules/*.yaml` by way of
`dpm/engine/`, always, and are fixed before AI ④ ever sees them.

## Every answer is checked before it is used

The pattern is the same in all four places: the model proposes, a
deterministic check disposes, and a rejected answer costs the output
nothing.

**AI ④** drops a paragraph whole — never a sentence out of it — when it
contains a number we did not measure, a signal name that does not exist,
a word that turns a description into a legal conclusion (`Verstoß`,
`rechtswidrig`, `unzulässig` …), or when it runs long. The Beweisakte is
complete without it: what carries a finding is the rulebook's text.

**AI ②** drops a row when the address does not occur in the document. An
industry it makes up costs the industry, not the target — a missing
industry is a blank a person fills in, an invented address is a site
nobody asked us to visit.

## Where it runs

Google **Gemini**, `gemini-2.5-flash-lite` by default. One environment
variable decides the backend; no code changes.

```bash
GEMINI_API_KEY=…                                    # AI Studio, free tier
DPM_VERTEX=1 GOOGLE_CLOUD_PROJECT=…                 # Vertex, billed to the credit
```

| Variable | Default | |
|---|---|---|
| `DPM_MODEL` | `gemini-2.5-flash-lite` | cheapest vision tier; none of the four tasks needs reasoning |
| `DPM_MIN_CONFIDENCE` | `0.7` | AI ①: below this a read signal becomes a `signal_error` |
| `GOOGLE_CLOUD_LOCATION` | `europe-west4` | Vertex only |

**Without a key everything still runs.** The capture takes the start page,
its screenshot and its hash, and every signal lands in `signal_errors` —
a valid partial capture, not a failure. `python -m dpm report` produces
the Beweisakte with no model text at all; `--zusammenfassung` is what asks
for AI ④, and it is off by default. The document handed over on Monday
therefore contains no machine-written sentence, which is a claim we can
make without qualification.

```bash
python -m dpm report data/fixtures/viagogo --zusammenfassung   # AI 4
python -m dpm zielliste kandidaten.xlsx                        # AI 2
```
