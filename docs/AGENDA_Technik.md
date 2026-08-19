# Tech Kickoff — Agenda

**Wed 19 Aug, evening · Donghyun + Karthik · ~60 min**
Read first: [`STRATEGIE.md`](STRATEGIE.md) §1 (what the consumer agency actually said), §4.2 (path-based capture), §5 (`capture.json`).

Everything here is a **decision to make tonight**, not a discussion to have later. After this meeting we work against files, not against each other.

---

## 0. Context in 60 seconds

The consumer agency (Verbraucherzentrale Bayern) held a seminar today. Three things came out of it that change what we build:

1. They want an **evidence file** (*Beweisakte*) — screenshots are the proof. Not an analysis, not a score.
2. **The interesting patterns are not on the landing page.** Their example: "*X people viewed this recently*" only appears after you click into a product. Same for missing VAT disclosure and checkout fees.
3. They want a **filterable table with statistics by industry and pattern type**, plus classification by legal provision.

Point 2 is the one that changes our architecture. Point 3 adds a second output.

They also named a test site: **viagogo**. That is our reference case.

---

## 1. Stack — decide now (15 min)

**Proposal: Node + TypeScript + Playwright (Chromium).**

| | Node + TS | Python |
|---|---|---|
| Signal measurement | DOM/CSS work — runs in the browser either way | same, but JS passed as a string, no type checking, no editor support |
| Chrome extension reuse | `extractors.js` becomes a content script **unchanged** | rewrite required |
| Report → PDF | Playwright already there, `page.pdf()` | extra dependency |
| One language across capture, engine, report, extension | yes | no |

The deciding argument is the extension: if we write measurements as plain browser JS with no Playwright dependency, the same file works in both worlds and the extension costs us a manifest and a popup instead of a rewrite.

**Counter-argument worth hearing:** if you are significantly faster in Python, that beats architectural elegance on a 5-day clock. Say so now, not on Friday.

**Decision → write it into `docs/DECISIONS.md` tonight.**

---

## 2. `capture.json` — freeze the schema (20 min)

This is the contract between us. Full proposal in [`STRATEGIE.md` §5](STRATEGIE.md). Three points need explicit agreement:

### 2.1 Every signal carries its own evidence

```jsonc
"signals": {
  "scarcity_value": { "wert": 3, "schritt": "produktdetail", "nachweis": "S-02.png" }
}
```

Not `"scarcity_value": 3`. Each measurement records **which step it came from and which screenshot proves it**.

*Why it matters:* this is the entire difference between a report and an evidence file. A finding in the Beweisakte must point at one specific screenshot. If the value is bare, I cannot bind it to evidence downstream, and the legal argument collapses.

### 2.2 Failed measurements go to `signal_errors`, never into `signals`

```jsonc
"signal_errors": { "price_at_checkout": "checkout not reachable without login" }
```

The rule engine then sets any rule needing that signal to `unklar` automatically. **Never write `null`, `0`, `false` or `-1` for "could not measure".** A `false` means "measured, and it is not there" — a completely different legal statement from "we could not check".

This is the one mistake that would quietly corrupt our results, so it is worth being pedantic about.

### 2.3 Determinism fields are mandatory

`viewport`, `locale: de-DE`, `timezone: Europe/Berlin`, `user_agent`, `dom_hash`, `timestamp`.

Pixel areas are meaningless without a fixed viewport, and reproducibility is our core claim against the ML approach. Fix these in code, do not leave them to defaults.

**Open question for us:** what exactly do we hash for `dom_hash`? Proposal: the serialized DOM after load and after cookie-banner interaction, normalized (strip nonces, timestamps, ad IDs) — otherwise every capture differs and the diff is useless. Needs 10 minutes of thought, not more.

---

## 3. Path-based capture — the real work (15 min)

A target is a **sequence of steps**, not a URL. Proposal `data/targets/viagogo.yaml`:

```yaml
name: viagogo
branche: Ticketing
start: "https://www.viagogo.de"
pfad:
  - schritt: startseite
  - schritt: suchergebnis
    aktion: suche
    wert: "Konzert München"
  - schritt: produktdetail
    aktion: klick_erstes_ergebnis
  - schritt: warenkorb
    aktion: klick
    selektor: "[data-testid=buy]"
```

Decisions needed:

- **How many step verbs do we support?** Proposal: `navigate`, `suche`, `klick`, `klick_erstes_ergebnis`, `scroll`, `warte`. Six. Not more — every extra verb is a feature nobody asked for.
- **Selectors live in the target file, never in code.** When viagogo changes its markup on Saturday, we edit YAML, not TypeScript.
- **What happens when a step fails?** Proposal: capture stops, everything measured so far is kept, remaining signals go to `signal_errors` with the step name. Partial captures are still useful — this is exactly how `unklar` should arise.
- **Who writes the target files?** Proposal: you write viagogo tonight as reference; the rest get written Thursday once we know which sites the legal team picked.

---

## 4. Division of labour (5 min)

| | |
|---|---|
| **Karthik** | capture layer: Playwright driver, path execution, `extractors.js`, network capture, screenshots, writes `capture.json` |
| **Donghyun** | rule engine (YAML → conditions → verdict), Beweisakte PDF, Marktübersicht with filters, evidence binding, timeline diff |

We touch different directories: `src/capture/**` vs `src/engine/**`, `src/report/**`. `src/signals/extractors.js` is yours; I only consume its output.

**Git convention proposal:** commit straight to `main`, small and often. No PR reviews between us — with two devs and five days, review latency costs more than it saves. The legal team uses PRs only if they feel unsure.

---

## 5. The one process decision that matters most (5 min)

**Walking skeleton before breadth.**

By Thursday evening, this chain must run end to end, even if each link is embarrassing:

```
viagogo → capture → ONE rule → ONE row in the table → PDF on disk
```

One rule. One signal. One row. Ugly is fine.

*Why:* everything after that is incremental, and every incremental step is independently demo-able. If instead we build a great capture layer and a great engine separately and join them Saturday, we find out on Saturday whether they fit — with no time left. And Monday's handover requires a non-developer to run the whole thing; that only works if the whole thing has existed for days.

**Concretely: no second signal until the first one has travelled the entire pipeline.**

---

## 6. Monday handover — design for it now (5 min)

Development stops Monday. We are unavailable Tue/Wed. A law student must run the demo alone on Thursday.

That is a **design constraint from day one**, not a Monday task:

- one command, one output folder — proposal: `npm run scan viagogo` → `out/viagogo/beweisakte.pdf`
- no environment variables, no API keys, no manual setup steps
- if it needs a running server, it needs a single start command and a fixed port
- error messages a non-developer can act on

**Decide tonight what that command is called.** Then build towards it, instead of retrofitting it Sunday night.

Insurance: recorded demo video **and** a hosted version, so the presentation does not depend on one laptop.

---

## 7. Polite retrieval (3 min)

Public pages only, no login, no bypassing access controls, visible rate limiting, honest user agent. A tool built to document legal violations must not obtain its evidence in a questionable way — and the legal team will be asked about this in the Q&A.

Agree on a delay between requests tonight (proposal: 2 s, and never more than one target in parallel). Cheap to do now, awkward to retrofit.

---

## 8. Open questions to settle

- [ ] Stack: Node+TS or Python
- [ ] Command name for the single entry point
- [ ] `dom_hash`: what exactly gets hashed and normalized
- [ ] Step verbs: which six
- [ ] Rate limit value
- [ ] Who writes `targets/viagogo.yaml` tonight
- [ ] Two backup sites in the same industry, in case viagogo blocks us
- [ ] Daily sync times (briefing says two × 15 min, morning and evening)

Write every answer into [`DECISIONS.md`](DECISIONS.md) before going to bed. Decisions that only exist in a chat window get re-discussed on Friday.

---

## What NOT to discuss tonight

Machine learning · a nice UI · user accounts · databases · mobile apps · pages behind login · the other 14 dark pattern categories · deployment platforms.

All of these are already decided or out of scope ([`STRATEGIE.md` §4](STRATEGIE.md), [`DECISIONS.md`](DECISIONS.md)). If one of them comes up, it goes in [`IDEAS.md`](IDEAS.md) and the meeting continues.
