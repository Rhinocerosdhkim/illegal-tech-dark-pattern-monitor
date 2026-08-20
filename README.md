# Dark Pattern Monitor — Team Illegal Tech

**Legal Loves Tech Hackathon 2026** · Challenge **VZ (III)** · Verbraucherzentrale Bayern
17.–21. August 2026 · München · <https://legallovestech.de/> · Präsentation: **Do, 27.08.**

> **„Dark Patterns zu finden ist einfach. Sie so zu dokumentieren, dass man handeln kann, ist schwer."**

Wir bauen **keinen KI-Richter**, sondern ein **Beweiserhebungs- und Strukturierungswerkzeug**: Es erhebt messbare Fakten von einer Webseite, prüft sie gegen ein von Jurist:innen geschriebenes Regelwerk und erstellt einen nachvollziehbaren Beweisbericht — Screenshot, Hash, Zeitstempel, Norm.

---

## Wo fange ich an?

| Ich bin … | Lies zuerst | Dann |
|---|---|---|
| **im juristischen Team** | [`rules/README.md`](rules/README.md) — die Anleitung fürs Regelwerk | [`CONTRIBUTING.md`](CONTRIBUTING.md) — wie ich hier eine Datei ändere, ohne Git zu können |
| **im Entwicklungsteam** | [Briefing §2–4](docs/briefing/Projekt-Briefing_DE.md) — Architektur & Signalliste | [`rules/_SIGNALE.md`](rules/_SIGNALE.md) — was wir zusagen zu messen |
| **neu dabei** | [Briefing DE](docs/briefing/Projekt-Briefing_DE.md) / [EN](docs/briefing/Project-Briefing_EN.md), Abschnitte 2, 3, 5, 6 | [`docs/DECISIONS.md`](docs/DECISIONS.md) — warum wir was entschieden haben |

> 📌 **[`docs/STRATEGIE.md`](docs/STRATEGIE.md) — Fassung 2.0, überarbeitet nach dem VZ-Seminar vom 19.08.** Marktlücke, Produktentscheidungen, Aufgabenteilung, Tagesplan. Alle lesen.
> 🔧 **[`docs/AGENDA_Technik.md`](docs/AGENDA_Technik.md)** — Agenda des Technik-Kickoffs (englisch).
> 🏗️ **[`docs/PRODUKT_Architektur.md`](docs/PRODUKT_Architektur.md)** — wie das Produkt abläuft: Verarbeitungskette, Oberfläche, **wo KI eingesetzt wird und wo nicht**, Baureihenfolge.

---

## Verarbeitungskette

```
Website → [1] CAPTURE  Screenshot, HTML, A11y-Tree, Netzwerk, Zeitstempel
        → [2] SIGNALE  messbare Fakten (px², Kontrast, Klicktiefe …)  ← deterministisch
        → [3] REGELWERK  ★ hier arbeitet das juristische Team ★       ← rules/*.yaml
        → [4] BEFUND   eindeutig / verdächtig / unklar / unauffällig
        → [5] ZEITACHSE  Vergleich mit früheren Erfassungen (Diff)
        → [6] BEWEISBERICHT  Screenshot + Hash + Zeitstempel + Norm + Begründung
```

Ein Sprachmodell wird an genau zwei eng begrenzten Stellen eingesetzt (mehrdeutige Formulierungen deuten, deutschen Berichtstext formulieren). **Die Befundentscheidung trifft es nie.**

---

## Stand des Regelwerks

| Regel | Muster | Norm | Status | Bearbeiter:in |
|---|---|---|---|---|
| [DP-001](rules/DP-001_Consent-Buttons.yaml) | Ungleiche Consent-Buttons | Art. 7 IV, 4 Nr. 11 DSGVO | ✅ FERTIG | *(Kickoff)* |
| [DP-002](rules/DP-002_Button-Loesung.yaml) | Button-Lösung | § 312j III, IV BGB | ✅ FERTIG | *(Kickoff)* |
| [DP-003](rules/DP-003_Dringlichkeit.yaml) | Vorgetäuschte Dringlichkeit | Anh. zu § 3 III UWG Nr. 7 | 🟡 ENTWURF | — |
| [DP-004](rules/DP-004_Kuendigungsbutton.yaml) | Fehlender Kündigungsbutton | § 312k BGB | 🟡 ENTWURF | — |
| [DP-005](rules/DP-005_Drip-Pricing.yaml) | Versteckte Kosten | PAngV, §§ 5, 5a UWG | 🟡 ENTWURF | — |
| [DP-006](rules/DP-006_Informationsverdeckung.yaml) | Informationsverdeckung | §§ 5, 5a UWG; Art. 246a EGBGB | 🟡 ENTWURF | — |

**Frist Paket 1 (Regelwerk): Donnerstag, 20.08., 18:00 Uhr.**
Trag dich in der Tabelle *und* im Feld `bearbeiter` der YAML-Datei ein. Bei knapper Zeit gilt: **vier saubere Regeln schlagen sechs halbfertige** — DP-005 und DP-006 entfallen zuerst.

---

## Arbeitspakete

| Paket | Inhalt | Frist | Ort im Repo |
|---|---|---|---|
| **1** | Regelwerk — 6 ausgefüllte Regeln | **Do 20.08., 18:00** | [`rules/`](rules/) |
| **2** | Gold Standard — ~20 Seiten von Hand bewertet | **Fr 21.08., 18:00** | [`data/gold-standard/`](data/gold-standard/) |
| **3** | Formulierungsrichtlinie, Haftungsabsicherung, 3 Folien | **Sa 22.08.** | [`docs/`](docs/) |

Details zu jedem Paket: [Briefing §6](docs/briefing/Projekt-Briefing_DE.md).

---

## Repo-Struktur

```
rules/                  ★ das Regelwerk — ist Produktlogik, nicht Dokumentation
  README.md               Anleitung fürs juristische Team
  _SIGNALE.md             alle messbaren Signale — nur daraus darf gewählt werden
  _VORLAGE.yaml           leere Vorlage
  DP-00X_*.yaml           die sechs Regeln
docs/
  challenge/              Challenge-Ausschreibung der Verbraucherzentrale
  briefing/               Projektbriefing DE + EN
  STRATEGIE.md            Marktlücke, Produktentscheidungen, Tagesplan
  PRODUKT_Architektur.md  Ablauf des Produkts, Oberfläche, KI-Einsatz, Baureihenfolge
  DECISIONS.md            Entscheidungslog — jede Entscheidung mit Datum und Begründung
  IDEAS.md                Ideenliste / future work
data/gold-standard/       Paket 2: Referenzbewertungen von Hand
```

`src/` legen wir an, sobald das Entwicklungsteam den Stack festgelegt hat.

---

## Bewusst nicht im Umfang

Vollautomatischer Kaufabschluss bis zur Zahlung · Seiten hinter Login · Mobile Apps · alle 20+ Dark-Pattern-Kategorien (wir nehmen sechs) · aufwendige Oberfläche · Nutzerkonten und Rechteverwaltung.

Gute Zusatzidee? → [`docs/IDEAS.md`](docs/IDEAS.md). Wir nennen sie in der Präsentation als Ausblick — gebaut wird sie nicht.

---

## English

Everything above in short: we build an **evidence tool**, not an AI judge. The legal team writes `rules/*.yaml`; the system executes those files directly. Field names are English, content is German (reports and presentation are in German) — if you prefer to draft in English, do so and mark it.

Start with [`rules/README.md`](rules/README.md), then read [`DP-001`](rules/DP-001_Consent-Buttons.yaml) and [`DP-002`](rules/DP-002_Button-Loesung.yaml) as worked examples. Full briefing: [Project-Briefing_EN.md](docs/briefing/Project-Briefing_EN.md).
