# Project Briefing: Dark Pattern and Design Monitor

**Legal Loves Tech Hackathon 2026 · Challenge VZ (III) · Verbraucherzentrale Bayern**

Version 1.0 · 19 August 2026 · For the whole team, especially our law students

> *This is the English version of `Projekt-Briefing_Dark-Pattern-Monitor_DE.md`. Both versions carry the same content. Legal terms are kept in German with an English explanation, since the deliverables themselves will be written in German.*

---

## 1. Why this document exists

Our team combines lawyers and developers. The two sides speak different languages and we are short on time. This document makes sure everyone has the same product in mind, and that each person knows exactly **what to deliver, by when, and in what format**.

Please read sections 2, 3, 5 and 6 in full. Those four contain everything directly relevant to the legal work.

---

## 2. What we are building — and what we deliberately are *not* building

### 2.1 The task

The challenge asks for a **website and design monitor** that analyses digital interfaces, detects dark patterns, documents changes over time, classifies suspicious design patterns, and prepares the results for **legal review, market observation and consumer information**.

The decisive detail is the list of intended users: consumer advice centres and associations, competitors, trade associations, chambers of commerce and crafts, data protection supervisory authorities, and the Federal Network Agency as Digital Services Coordinator.

**Every one of these is a legal actor — not a consumer.** They do not need a tool that tells them "this site is bad". They need a tool that does the hard part for them: **documenting a violation in a way that holds up.**

### 2.2 Our core thesis

> **Detecting dark patterns is easy. Documenting them so they are legally usable is hard.**

From this follows our product definition:

> Our system is **not an AI judge** deciding whether a violation exists. It is an **evidence-gathering and structuring tool** that prepares the factual basis so a lawyer can perform the legal assessment (*Subsumtion*) themselves.

### 2.3 The anti-pattern (what other teams will build)

Several teams will very likely build this:

> Screenshot of a page → send to a language model → "find dark patterns" → output a list

That takes 30 minutes and fails for four reasons:

1. **Not reproducible.** Same input twice, different result twice.
2. **Not justifiable.** Asked "what is this based on?", the answer is "the model said so". Worthless in a legal proceeding.
3. **No time dimension.** The challenge explicitly requires *documenting changes*. A one-off scan cannot do that.
4. **Legally risky.** Wrongly asserting a legal violation can itself be unlawful (see section 6, Packet 3).

So we take a different route.

### 2.4 Our approach: signals → rulebook → verdict

```
    Website
       │
       ▼
[1] CAPTURE              Screenshot, HTML, accessibility tree,
                         network traffic, timestamp
       │
       ▼
[2] SIGNALS              Measurable facts, purely technical:
                         button area in px², contrast ratios, click count,
                         button labels, pre-ticked checkboxes ...
       │                 → deterministic, reproducible at any time
       ▼
[3] RULEBOOK             ★ THIS IS WHERE THE LEGAL TEAM WORKS ★
                         Signals are mapped to elements of a legal
                         provision. Output: norm + verdict level
       │
       ▼
[4] VERDICT              eindeutig / verdächtig / unklar / unauffällig
                         (clear / suspected / unclear / unremarkable)
       │
       ▼
[5] TIMELINE             Comparison against earlier captures (diff)
       │
       ▼
[6] EVIDENCE REPORT      Screenshot + hash + timestamp + legal provision
                         + traceable reasoning
```

A language model is used at only two tightly bounded points: interpreting ambiguous wording, and phrasing the German report text. **It never makes the verdict decision.**

---

## 3. The key translation task

This is the intellectual core of the project — and it is a legal task, not a technical one.

### 3.1 Every legal provision is already an if-then structure

For the developers on the team, in their language:

| German legal term | Code equivalent |
|---|---|
| **Tatbestand** (statutory definition of the offence) | the whole `if` condition |
| **Tatbestandsmerkmal** (individual element of that definition) | a single sub-condition |
| **Rechtsfolge** (legal consequence) | the `then` block |
| **Subsumtion** (applying facts to the definition) | evaluating the condition against actual facts |

Law students are trained to decompose provisions into their elements. That is exactly the skill we need — we just write the result into a structured file instead of a legal memo.

### 3.2 The guiding question

Instead of asking "is this a violation?", we consistently ask:

> **"What conditions must be true on screen for this element of the provision to be satisfied — and can each of those conditions be answered with yes/no or a number, using only a screenshot and the HTML?"**

### 3.3 Three tests for every condition

Before a condition goes into the rulebook, it must pass all three:

1. **Machine-observable?** Can it be answered from screenshot and HTML alone? If it would require a contract document, a conversation, or knowledge of internal processes → leave it out, or classify it as "unklar".
2. **Unambiguously decidable?** Yes/no or a number. Wording like "inappropriate", "sufficiently clear" or "in the individual case" is unusable without a concrete threshold.
3. **Traceable?** If challenged, can we trace the verdict back to the provision?

### 3.4 Worked example

**Provision:** Art. 7(4) in conjunction with Art. 4(11) GDPR — consent must be freely given.

**Legal reasoning step:** Freely given consent requires that refusing is not noticeably harder than accepting (see also Recitals 32, 42).

**Translation into measurable signals:**

| Condition | Signal | Threshold |
|---|---|---|
| Refusing requires more interaction steps | `reject_click_depth` | `> 1`, while accepting takes one click |
| Accept button noticeably larger | `accept_button_area_px2 / reject_button_area_px2` | `> 2.0` |
| Refusal visually de-emphasised | difference in contrast ratios | `> 3.0` |
| Pre-ticked consent boxes | `preselected_checkbox_count` | `> 0` |

This table — for six patterns — *is* our rulebook.

---

## 4. The interface between law and code: the rulebook

So both sub-teams can work **in parallel** without waiting on each other, there is exactly one binding interface: a rules file in YAML format.

```
              rules/*.yaml
                   ▲
      written by   │   read by
      legal team   │   dev team
```

**This file is not documentation. It is the product logic.** Whatever is written there is executed directly by the system.

### 4.1 Structure of a rule

Field names and content stay in German — the reports and the presentation will be in German.

```yaml
- id: DP-001
  name_de: "Ungleiche Gestaltung der Consent-Buttons"

  legal_basis:                    # provisions, as precise as possible
    - "Art. 7 Abs. 4 DSGVO"
    - "Art. 4 Nr. 11 DSGVO"
    - "ErwG 32, 42 DSGVO"

  tatbestand_de: >                # one or two sentences, plain language
    Eine Einwilligung ist nur wirksam, wenn sie freiwillig erteilt wird.
    Freiwilligkeit setzt voraus, dass die Ablehnung nicht erschwert ist.

  signals:                        # ONLY from the signal list in 4.2
    - accept_button_area_px2
    - reject_button_area_px2
    - reject_click_depth
    - accept_contrast_ratio
    - reject_contrast_ratio
    - preselected_checkbox_count

  verdict_rules:
    eindeutig:                    # hard to dispute
      - "reject_click_depth > 1"
      - "accept_button_area_px2 / reject_button_area_px2 > 2.0"
    verdaechtig:                  # indication, room for interpretation
      - "accept_contrast_ratio - reject_contrast_ratio > 3.0"
      - "preselected_checkbox_count > 0"
    # nothing matches → automatically "unauffällig"

  threshold_source: >             # where does the threshold come from?
    Eigene Festlegung des Teams, keine Rechtsprechungsgrundlage.
    Begründung: Faktor 2 als konservative Untergrenze gewählt.

  explanation_template_de: >      # appears verbatim in the report
    Der Ablehnen-Button misst {reject_button_area_px2} px²,
    der Zustimmen-Button {accept_button_area_px2} px².
    Die Ablehnung erfordert {reject_click_depth} Interaktionsschritte.
    Dies begründet den Verdacht einer nicht freiwillig erteilten Einwilligung.

  disclaimer_required: true
```

### 4.2 The most important rule when filling this in

> **The `signals` field may only contain entries from the list below.**

This list is everything our system can technically measure. If you need a signal that is not on it, clear it with the dev team **first** — it may not be feasible in the time available.

**Available signals:**

*Buttons and controls*
- `accept_button_area_px2`, `reject_button_area_px2` — area in pixels
- `accept_contrast_ratio`, `reject_contrast_ratio` — WCAG contrast ratio
- `reject_click_depth` — interaction steps needed to fully refuse
- `button_label_text` — the label, verbatim
- `preselected_checkbox_count` — number of pre-ticked boxes

*Text and notices*
- `has_zahlungspflichtig_label` — yes/no (the mandatory "payment obligation" button wording)
- `has_kuendigungsbutton` — yes/no (the mandatory cancellation button)
- `countdown_element_present` — yes/no
- `countdown_resets_on_revisit` — yes/no (verified by revisiting)
- `scarcity_text_present` — yes/no (e.g. "only 2 left")

*Prices*
- `price_listed`, `price_at_checkout`, `price_delta`

*Concealment of information*
- `hidden_by_opacity_count`, `font_size_min_px`, `scroll_depth_of_required_info`

*Network*
- `third_party_cookies_before_consent` — count before consent is given

---

## 5. The six patterns in scope

We deliberately handle **six** patterns thoroughly rather than twenty superficially.

| ID | Pattern | Legal hook | Difficulty |
|---|---|---|---|
| DP-001 | Unequal consent buttons | Art. 7(4), Art. 4(11) GDPR; Rec. 32, 42, 43 | medium |
| DP-002 | Missing or unclear order button wording | § 312j(3), (4) BGB | low, very clear-cut |
| DP-003 | Fake urgency / scarcity | Annex to § 3(3) UWG (esp. no. 7); §§ 5, 5a UWG | low to medium |
| DP-004 | Missing cancellation button | § 312k BGB | low, very clear-cut |
| DP-005 | Hidden costs / drip pricing | PAngV; §§ 5, 5a UWG | medium |
| DP-006 | Concealment of mandatory information | §§ 5, 5a UWG; Art. 246a EGBGB with § 312d BGB | high |

### Notes on individual patterns

**DP-002 and DP-004** are our most reliable patterns: the presence of a specific label or a specific control can be determined technically with near-zero error. Both are excellent for the live demo.

**DP-003**: the real proof is not that a countdown exists, but that it **resets when the page is revisited**. We can demonstrate exactly that automatically — and that is precisely the hook into the blacklist of per-se unfair practices.

**Art. 25 DSA** is deliberately *not* a standalone pattern. Reason: Art. 25(2) DSA carves out situations already covered by the Unfair Commercial Practices Directive (implemented in the UWG) or the GDPR. Asserting a standalone DSA violation would therefore be attackable in many cases. **We will mention Art. 25 DSA in the presentation as an overarching frame and as future work — but not as a basis for our verdicts.** If someone on the legal team wants to challenge or deepen this assessment with sources: very welcome, it would be a strong point in the Q&A.

---

## 6. Work packets for the legal team

Three packets with fixed deadlines. Please treat them as binding — the dev team depends on them directly.

---

### 📦 Packet 1 — Rulebook

**Deadline: Thursday 20 Aug, 18:00**

**Deliverable:** six fully completed rules in the format above.

**How:**
- DP-001 and DP-002 we build together in the kickoff workshop as templates.
- DP-003 to DP-006 are split within the legal team (one or two patterns per person).
- DP-006 should go to whoever is most confident in unfair competition law (*Lauterkeitsrecht*).

**Three binding constraints:**

1. **Only use signals from the list in section 4.2.** If something is missing, ask first.
2. **Every condition needs a concrete value.** "Inappropriately large" is unusable; "factor 2.0" is usable. If there is a basis for the value in case law, guidelines or literature, note it in `threshold_source`. If there is none, write honestly "eigene Festlegung des Teams" (our own determination). **That is entirely fine.** What matters is transparency; we will say so openly in the presentation.
3. **`eindeutig` is only for what is hard to dispute.** When in doubt, drop it one level. A system that judges cautiously is far more useful to a consumer advice centre than one that overstates.

**If time runs short:** four solid rules beat six half-finished ones. Flag it early and we will prioritise together.

---

### 📦 Packet 2 — Gold standard reference set

**Deadline: Friday 21 Aug, 18:00**

**Deliverable:** a spreadsheet of roughly 20 websites assessed **by hand** against our own rulebook.

**Columns:**

| URL | Pattern ID | Human verdict | Evidence (screenshot) | Note |
|---|---|---|---|---|

Verdict values: `eindeutig` / `verdächtig` / `unauffällig`

**Why this matters:** only with this reference can we make a defensible claim about accuracy in the presentation. A team with a traceable measurement is far more convincing than one with just a demo.

**Selection criteria:**
- reachable without login
- German-language
- **about half should be unremarkable sites.** This is critical: we need to measure how often our system raises a false alarm. A system that sees violations everywhere is worthless.

**The dev team will supply a pre-checked candidate list by Thursday morning**, so you only assess sites that can actually be captured technically.

---

### 📦 Packet 3 — Legal safeguards and presentation content

**Deadline: Saturday 22 Aug**

Three deliverables:

**a) Wording policy and liability safeguards**

The core question: what statements is our system even allowed to make?

Wrongly asserting a legal violation can damage a company's reputation and trigger unfair-competition claims **against us** (hooks: § 4 nos. 1 and 2 UWG, possibly §§ 823, 824 BGB). So we need:

- a binding word list: which terms do we use at which verdict level? (proposal for discussion: `eindeutig` → "Prüfhinweis mit hoher Auffälligkeit", `verdächtig` → "Verdachtsmoment"; avoid the word "Verstoß" as a finding of fact wherever possible)
- the disclaimer text, verbatim, that appears in every report
- a short assessment of the lawfulness of automated retrieval of publicly accessible pages (observing public content, no circumvention of access controls, no server overload)

**b) Justification of the three-level verdict model**

Two or three sentences that can be delivered in the presentation: why do we distinguish `eindeutig`, `verdächtig` and `unklar` — and why is the "unklar" level a quality feature rather than an admission of weakness? This point demonstrates legal maturity to the jury.

**c) Three presentation slides**

1. Mapping of patterns to legal provisions
2. Evidentiary value: why our reports are usable
3. Limits of the system and outlook

> ⚠️ **Packet 3 must be finished by Saturday.** From Tuesday the dev team is unavailable (see section 7). Anything still open after that cannot be implemented in the product.

---

## 7. Timeline

The presentation is on **Thursday 27 August**. The dev team is unavailable from **Tuesday 25 August**.

Therefore: **code must be finished Sunday evening. Monday is not a development day, it is a handover day.**

| Day | Dev team | Legal team | Together |
|---|---|---|---|
| **Wed 19** | Capture layer (screenshot, HTML) | Onboarding, start Packet 1 | Kickoff workshop: build DP-001 and DP-002 together |
| **Thu 20** | Signal extraction, rule engine | **Packet 1 due, 18:00** | Evening: run the rulebook through the system for the first time |
| **Fri 21** | Countdown verification, price comparison, report structure | **Packet 2 due, 18:00** | Afternoon: system vs. human verdicts, first accuracy numbers |
| **Sat 22** | Timeline/diff, evidence report, UI | **Packet 3 due** | 23:00: feature freeze — no new functionality after this |
| **Sun 23** | Bug fixing, deployment, demo recording | Draft presentation | 3× full dress rehearsal |
| **Mon 24** | **Handover**, documentation, Q&A brief | Rehearse presentation | Final rehearsal; the team must be able to run the demo **without** the dev team |
| Tue 25 – Wed 26 | *unavailable* | Polish presentation | – |
| **Thu 27** | – | – | **Presentation** |

### What this means for you concretely

By Monday evening, this sentence must be true:

> *Any team member can run the demo end to end on their own and answer the ten most likely follow-up questions.*

We will test exactly that on Monday: one person from the legal team runs the demo alone. Wherever it stalls, we document further.

As additional insurance: a **recorded video of the demo** and a **version reachable online**, so the presentation does not depend on one particular laptop.

---

## 8. What we deliberately leave out

Being clear about exclusions matters as much as being clear about scope.

**Out of scope:**
- full automation of a purchase flow through to payment
- pages behind a login
- mobile apps
- all common dark pattern categories (there are well over twenty — we handle six)
- an elaborately designed user interface
- user accounts, permissions, multi-tenancy

If a good extra idea comes up during the work: please put it in the idea list. We will mention it in the presentation as future work — but we will not build it.

---

## 9. How we work day to day

**Two short syncs daily, 15 minutes each** (morning and evening). Three questions:
1. What got **finished** since yesterday? (not "what am I working on")
2. What will be finished today?
3. Where are you blocked — especially: are you waiting on the other sub-team?

**Decision log:** every decision, with date and reasoning, in one shared file. Example: *"20 Aug — Art. 25 DSA not used as a standalone verdict pattern, because Art. 25(2) DSA makes it subsidiary to the UWG and GDPR."* This prevents re-running the same discussion and gives us material for the Q&A.

**One request to the legal team:** when a question comes from the dev side, the most useful answer is rarely a paragraph of prose. What helps is a list of conditions answerable with yes/no or a number. If a question cannot be answered that way, that is also an important result — the element then belongs in the "unklar" level, and that is a deliberate, defensible decision.

---

## 10. Our line of argument for the presentation

One sentence everything aligns to:

> **"Finding dark patterns is easy. Documenting them so you can act on them is hard."**

Three pieces of evidence for it:

1. **Beweisfähigkeit (evidentiary value)** — every finding carries a screenshot, a hash of the page state, a timestamp and the legal provision. The output is prepared so it can be attached to a formal cease-and-desist letter (*Abmahnung*).

2. **Nachvollziehbarkeit (traceability)** — every verdict traces back cleanly: measured signal → condition in the rulebook → legal provision. No finding rests on an unverifiable model decision. The three-level model deliberately prevents overstatement.

3. **Zeitachse (time dimension)** — we are not building a scanner, we are building a **monitor**. We also detect when a company quietly reintroduces a design it had agreed to stop using. That connects directly to enforcement of cease-and-desist undertakings.

---

## 11. Kickoff meeting checklist for today

- [ ] Timeline and the 25 Aug unavailability known to everyone
- [ ] Attendance at the 27 Aug presentation clarified
- [ ] Product definition agreed in one sentence
- [ ] DP-001 and DP-002 built together as templates
- [ ] Signal list confirmed, requests for additions noted
- [ ] Packet 1 assigned to individuals
- [ ] Candidate sites roughly scoped
- [ ] Decision: are companies named in the presentation or anonymised? *(recommendation: anonymise — "Shop A", "Provider B" — unless already publicly criticised)*
- [ ] Presenters chosen *(recommendation: one person from each sub-team)*
- [ ] Shared drive, decision log and idea list set up
- [ ] Daily sync times fixed

---

## Appendix: German legal terms you will hear

| Term | Meaning |
|---|---|
| Verstoß | violation, infringement |
| Prüfschema | assessment checklist / order of examination — for us: the rulebook |
| Abmahnung | formal warning letter demanding a practice be stopped |
| Unterlassungserklärung | binding undertaking to cease the practice; breach triggers a contractual penalty |
| Anspruchsgrundlage | the provision a claim is based on |
| Erwägungsgrund (ErwG) | recital — interpretive guidance in the preamble of EU legislation |
| Rechtsprechung / Urteil / Aktenzeichen | case law / judgment / case reference number |
| h. M. (herrschende Meinung) | prevailing opinion in legal scholarship |
| str. (streitig) | disputed — for us, a trigger for the "unklar" level |
| Beweisfähigkeit | suitability to serve as evidence in proceedings |
| UWG | Act Against Unfair Competition |
| BGB | German Civil Code |
| PAngV | Price Indication Ordinance |
| DSGVO | GDPR |
| EGBGB | Introductory Act to the Civil Code |
