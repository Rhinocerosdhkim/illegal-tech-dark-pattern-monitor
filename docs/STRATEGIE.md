# Strategie und Tagesplan

**Fassung 2.0 · Stand 19.08.2026 abends** — überarbeitet nach den Seminarnotizen der Verbraucherzentrale Bayern
Entwicklungszeit bis **Mo 24.08.** · Präsentation **Do 27.08.**
Team: 2× Entwicklung (Donghyun, Karthik) · 2× Recht (Sebastian, +1)

---

## 1. Was die Verbraucherzentrale tatsächlich gesagt hat

Aus dem Seminar am 19.08. liegen Notizen vor. Sie sind wichtiger als jede Vermutung, die wir vorher angestellt haben, und ändern das Produkt an drei Stellen.

### 1.1 Das Wort lautet „Beweisakte", nicht „Bericht"

> *„Nachweis für das Tool: **Screenshot!**"*
> *„Erstellen einer **Beweisakte** mit Screenshots und gegen was dieses Dark Pattern verstoßen könnte"*

Beides war in den Notizen hervorgehoben. Damit ist bestätigt, was wir vermutet hatten — aber die Wortwahl ist schärfer als unsere. **Wir nennen die Ausgabe ab sofort Beweisakte.** Nicht Report, nicht Bericht, nicht Analyse. Der Begriff transportiert genau, was das Produkt leistet, und er ist die Sprache der Adressatin.

Ebenso bemerkenswert: *„gegen was dieses Dark Pattern verstoßen **könnte**"*. Der Konjunktiv kommt von der Verbraucherzentrale selbst. Sie will keine Feststellung eines Verstoßes durch die Maschine — sie will die Grundlage, um selbst zu entscheiden. Unser Dreistufenmodell trifft genau diesen Bedarf.

### 1.2 Sie haben eine eigene Kategorisierung

> *Zeitdruck · Zwang · Hindernisse · Irreführung*

Das ist ihr Denkmodell. Unsere Regeln heißen DP-001 bis DP-006 — für uns praktisch, für die Adressatin bedeutungslos. **Jede Regel bekommt deshalb ein Feld `kategorie` mit genau einem dieser vier Werte.** Danach wird gefiltert und statistisch ausgewertet.

| Kategorie | Unsere Regeln |
|---|---|
| **Zeitdruck** | DP-003 Countdown, Knappheitshinweise, „X Personen sehen sich das an" |
| **Zwang** | DP-001 ungleiche Consent-Buttons, Kopplung |
| **Hindernisse** | DP-004 fehlender Kündigungsbutton, erschwerte Ablehnung (`reject_click_depth`) |
| **Irreführung** | DP-002 Button-Lösung, DP-005 Preis/MwSt, DP-006 Informationsverdeckung |

### 1.3 „Pur-Abos sind derzeit noch legal"

Ausdrücklich notiert: Bezahlmodelle nach dem Muster *Einwilligung oder Abo* sind **gegenwärtig zulässig**. Das ist eine Warnung, keine Aufgabe.

**Wir bauen dafür keine Regel, die anschlägt.** Wer ein noch zulässiges Geschäftsmodell als Verstoß ausweist, verliert die Glaubwürdigkeit — und wird selbst angreifbar (§ 4 Nr. 1, Nr. 2 UWG). Höchstens als reine **Beobachtungsnotiz ohne Befundstufe** in der Marktübersicht.

*Aufgabe fürs juristische Team:* eine belastbare Fundstelle zum aktuellen Stand (Stichwort EDSA-Stellungnahme zu „Consent or Pay") — zwei Sätze reichen. Das ist eine sichere Antwort auf eine sehr wahrscheinliche Jury-Frage.

### 1.4 Sie haben uns ein Testobjekt genannt

> *„An Seite **viagogo** testen (Ticketverkaufseite)"*

Das löst unser größtes Risiko. Wir mussten bis heute Abend Seiten finden, auf denen unsere stärksten Muster überhaupt vorkommen — **die Adressatin hat uns die Seite selbst genannt.** Ticketzweitmarkt vereint mutmaßlich Zeitdruck, Knappheit, Betrachterzahlen und Gebühren, die erst spät sichtbar werden.

**viagogo wird unser Referenzfall.** Die gesamte Pipeline wird zuerst an dieser einen Seite zum Laufen gebracht, danach verbreitert.

> ⚖️ *Aufgabe fürs juristische Team, vor der Präsentation:* Ist viagogo bereits öffentlich beanstandet worden, mit belegbarer Fundstelle? Nur dann nennen wir den Namen auf den Folien — sonst „Ticketplattform A". **Bitte nichts behaupten, was wir nicht belegen können.**

### 1.5 Die technische Schwierigkeit, die sie benannt haben

> *„sowas wie ‚so viele Nutzer haben sich das Produkt zuletzt angeschaut' erst sichtbar, wenn man auf das Produkt klickt"*
> *„keine Mehrwertsteuer-Angabe oder versteckt in Kopfzeile"*

Das ist die wichtigste technische Aussage des ganzen Seminars: **Die interessanten Muster stehen nicht auf der Startseite.** Sie erscheinen erst auf der Produktdetailseite, im Warenkorb, im Bestellvorgang.

Ein Werkzeug, das nur eine URL aufruft und misst, findet sie nicht. Siehe Abschnitt 4.2 — das ändert die Erfassungsschicht grundlegend.

### 1.6 Die Ausgabe, die sie sich vorstellen

> *„**Tabelle** (z. B. PDF) mit **Filtermöglichkeit** und **Statistiken** (Branche, Art), Norm klassifizieren"*

Ebenfalls hervorgehoben. Und es ist mehr, als wir bisher geplant hatten: nicht nur eine Akte je Seite, sondern eine **auswertbare Übersicht über viele Seiten**, filterbar nach Branche und Art des Musters, mit Zuordnung zur Norm.

Damit ist der dritte in der Challenge genannte Zweck bedient, den wir bisher stiefmütterlich behandelt haben: **Marktbeobachtung.**

---

## 2. Das Produkt hat zwei Ausgaben, nicht eine

| | **Beweisakte** | **Marktübersicht** |
|---|---|---|
| Bezugsgröße | eine Seite, ein Befund | viele Seiten |
| Zweck | Anlage zur Abmahnung | Marktbeobachtung, Schwerpunktsetzung |
| Adressat | Rechtsabteilung, Gericht | Referatsleitung, Presse, Aufsicht |
| Format | PDF, festgeschrieben | HTML mit Filtern, Export nach PDF und CSV |
| Inhalt | Screenshot, Hash, Zeitstempel, gemessener Wert, Norm, Anspruchskette | Zählungen nach Branche, Kategorie, Norm, Zeitverlauf |
| Fertig bis | **Fr 21.08.** | **Sa 22.08.** |

Beide speisen sich aus denselben Erfassungsdaten. Ist die Beweisakte gebaut, ist die Übersicht im Wesentlichen Aggregation.

**Und die Daten dafür haben wir schon eingeplant:** Der Gold Standard aus Paket 2 sind genau die 20 Seiten, aus denen die Marktübersicht entsteht. Aus einer Messaufgabe wird zugleich der Demo-Inhalt.

### Zielausgabe Beweisakte

| Nr. | Befund | Gemessener Wert | Kategorie | Norm | Stufe | Nachweis |
|---|---|---|---|---|---|---|
| 1 | Countdown springt nach Löschen aller Browserdaten auf denselben Startwert | `countdown_resets_on_revisit = true`, Startwert 900 s | Zeitdruck | Anh. zu § 3 Abs. 3 UWG Nr. 7 | eindeutig | S-02, S-03 · 2 Messungen · `sha256:a1b2…` |
| 2 | Ablehnung erfordert mehr Schritte als Zustimmung | `reject_click_depth = 3` (Zustimmung 1) | Hindernisse | Art. 7 Abs. 4 DSGVO | eindeutig | S-01 · 19.08.2026 14:22:03 |
| 3 | Kein Hinweis auf Umsatzsteuer im Preisumfeld | `vat_disclosure_present = false` | Irreführung | § 6 PAngV → § 3a UWG | verdächtig | S-04 · Produktdetailseite |

### Zielausgabe Marktübersicht

Filter: Branche · Kategorie · Norm · Befundstufe · Zeitraum.
Statistik: Befunde je Branche, häufigste Kategorie, häufigste Norm, Veränderung gegenüber der letzten Erfassung.

---

## 3. Die Marktlücke

Aus dem Seminar: Die bestehenden Werkzeuge werden **nicht wegen fehlender Funktionen nicht eingesetzt, sondern weil sie nicht ins Budget passen.**

| Angebot | Was es ist | Warum es für eine VZ nicht taugt |
|---|---|---|
| **FairPatterns** (Paris) | SaaS + Beratung, Figma-Plugin, KI-Agent. Kunden: HP, Wolters Kluwer, Bird & Bird | Enterprise-Preismodell, kein öffentlicher Preis. Liefert **Design-Empfehlungen** — Adressat sind Unternehmen, die sich absichern wollen, nicht Stellen, die durchsetzen wollen |
| **R Systems** | kommerzielles Enterprise-Angebot eines IT-Dienstleisters | Projektgeschäft, Preis auf Anfrage. Gleiche Adressatenrichtung |
| **UIGuard** ([arXiv 2308.05898v2](https://arxiv.org/html/2308.05898v2)) | Forschungsprototyp: Computer Vision + NLP auf **Mobile Apps**, Precision 0,83 / Recall 0,82 | Kein Produkt, kein Web, kein Recht. ML-basiert — **jeder sechste Befund falsch**, als Abmahnungsgrundlage unbrauchbar |
| **rajnish159/Dark-Pattern-Detection** | regelbasierte Browser-Extension, JavaScript | 1 Stern, 3 Commits. **Keine Lizenzangabe → Code rechtlich nicht nachnutzbar.** Reine Klassifikation |

**Keines** erzeugt eine Beweisakte. Alle sagen „hier ist ein Dark Pattern". Keines sagt „hier der gemessene Wert, hier die Norm, hier Zeitstempel und Hash — und am 14.08. war es noch anders".

> ### Kernthese
> **„Dark Patterns zu erkennen können andere längst. Sie bezahlbar und abmahnfähig zu dokumentieren kann niemand."**

Drei Belege: **bezahlbar** (Open Source, läuft auf einem VZ-Laptop, keine Lizenzkosten) · **abmahnfähig** (Beweisakte statt Werturteil) · **Zeitachse** (erkennt, wenn ein Design still wieder eingeführt wird — Anschluss an die Durchsetzung von Unterlassungserklärungen).

---

## 4. Produktentscheidungen

### 4.1 Headless zuerst, Chrome-Erweiterung als Aufsatz

Der Extension-Vorschlag aus dem Team ist für die **Verbreitung** richtig, für den **Kern** nicht: Eine Extension läuft nur, wenn ein Mensch die Seite besucht — das von der Challenge verlangte Monitoring über Zeit kann sie nicht leisten. Ebenso wenig den Countdown-Nachweis, der einen sauberen Browserzustand braucht.

**Der Kniff:** Alle Signalmessungen werden als **reines Browser-JavaScript ohne Playwright-Abhängigkeit** geschrieben (`src/signals/extractors.js`). Playwright führt sie über `page.evaluate()` aus; dieselbe Datei läuft unverändert als Content Script. Die Extension kostet dann nur noch Manifest und Popup — ein Sonntagnachmittag, wenn wir vorne liegen; entfällt ohne Verlust, wenn nicht.

### 4.2 Erfassung entlang eines Pfades, nicht einer URL — **neu**

Folgt zwingend aus 1.5. Ein Ziel ist keine URL, sondern eine **Schrittfolge**:

```
Startseite → Suche/Kategorie → Produktdetailseite → Warenkorb → Bestellübersicht
```

Jeder Schritt erzeugt einen eigenen Screenshot und einen eigenen Satz Messwerte. Ein Ziel wird in `data/targets/<name>.yaml` beschrieben:

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

Der Pfad wird je Seite von Hand einmal festgelegt. Das ist unspektakulär, aber ehrlich — und es ist der Grund, warum wir Muster finden, die ein Startseiten-Scanner nie sieht. **In der Präsentation ist genau das ein Punkt:** wir haben die Schwierigkeit, die die Verbraucherzentrale benannt hat, tatsächlich gelöst.

### 4.3 Umfang: DP-001 bis DP-004 plus der einfache Teil von DP-005

DP-005 wird **geteilt**, weil das Seminar die Mehrwertsteuer-Angabe ausdrücklich genannt hat:

- **DP-005a — Preisangabe auf der Produktseite** (MwSt-Hinweis vorhanden? wo? Versandkosten genannt?): reine Textsuche im Preisumfeld, in zwei Stunden gebaut → **kommt rein**
- **DP-005b — Drip Pricing bis zum Bestellabschluss** (Preisdifferenz Liste vs. Kasse): setzt vollständige Navigation bis zur Kasse voraus, fragil → **nur bei Restzeit**

DP-006 bleibt bei Restzeit. Niemand fängt damit an, solange DP-003 und DP-004 nicht auf `REVIEW` stehen.

### 4.4 Kein Code aus rajnish159 · Kein ML im Befund · Keine Datenbank

Unverändert. Ohne Lizenzangabe gilt das Urheberrecht vollumfänglich — wir sehen uns das Repository als Ideengeber an und schreiben alles selbst. Ein Erfassungslauf = eine JSON-Datei plus Screenshots; die Zeitachse ist ein Vergleich zweier Dateien.

### 4.5 Abrufe bleiben zurückhaltend

Wir rufen ausschließlich öffentlich zugängliche Seiten ab, umgehen keine Zugangssperren, melden uns nicht angemeldet an und begrenzen die Abrufrate spürbar. Das ist keine Formalie: Ein Werkzeug, das Rechtsverstöße dokumentieren soll, darf sich seine Beweise nicht auf angreifbarem Weg beschaffen. Gehört in Paket 3 und auf eine Folie.

---

## 5. Technische Schnittstelle: `capture.json`

Zwischen Recht und Technik steht `rules/*.yaml`. Zwischen den beiden Entwicklern steht `capture.json`. **Heute festlegen, danach nicht mehr anfassen.**

```jsonc
{
  "meta": {
    "ziel": "viagogo",
    "branche": "Ticketing",
    "start_url": "https://www.viagogo.de",
    "timestamp": "2026-08-19T14:22:03+02:00",
    "capture_mode": "headless",
    "viewport": { "width": 1440, "height": 900 },
    "locale": "de-DE", "timezone": "Europe/Berlin",
    "user_agent": "...",
    "run_id": "2026-08-19T14-22-03_viagogo"
  },

  "schritte": [
    { "schritt": "startseite",   "url": "...", "screenshot": "S-01.png", "dom_hash": "sha256:..." },
    { "schritt": "produktdetail","url": "...", "screenshot": "S-02.png", "dom_hash": "sha256:..." }
  ],

  // Jeder Messwert weiß, WO er gemessen wurde. Das ist der Unterschied
  // zwischen einem Bericht und einer Beweisakte.
  "signals": {
    "countdown_element_present": { "wert": true,  "schritt": "produktdetail", "nachweis": "S-02.png" },
    "scarcity_value":            { "wert": 3,     "schritt": "produktdetail", "nachweis": "S-02.png" },
    "reject_click_depth":        { "wert": 3,     "schritt": "startseite",    "nachweis": "S-01.png" },
    "vat_disclosure_present":    { "wert": false, "schritt": "produktdetail", "nachweis": "S-02.png" }
  },

  "signal_errors": {
    "price_at_checkout": "Bestellabschluss ohne Anmeldung nicht erreichbar"
  }
}
```

**Die wichtigste Regel:** Was nicht gemessen werden konnte, steht **nicht** in `signals`, sondern mit Begründung in `signal_errors`. Die Regel-Engine setzt jede Regel, die ein fehlendes Signal braucht, automatisch auf `unklar`. Die dritte Stufe entsteht so technisch von selbst.

### Stack

Node + TypeScript + Playwright (Chromium) · `js-yaml` fürs Regelwerk · Beweisakte als HTML → PDF über Playwright · kein `eval()`, sondern ein kleiner eigener Vergleichsparser für `> < >= <= == != and`.

Begründung für JavaScript statt Python: Die Signalmessung ist DOM- und CSS-Arbeit und muss ohnehin im Browser laufen. Mit JS gibt es keine Sprachgrenze zwischen Messung, Extension und Ausgabe. *— Noch nicht endgültig entschieden, siehe [`AGENDA_Technik.md`](AGENDA_Technik.md).*

---

## 6. Aufgabenteilung

### Entwicklung

| | Verantwortlich für |
|---|---|
| **Karthik** | Erfassungsschicht: Playwright-Steuerung, **Pfadabarbeitung**, `extractors.js`, Netzwerkmitschnitt, Screenshots, `capture.json` schreiben |
| **Donghyun** | Regel-Engine, **Beweisakte**, **Marktübersicht**, Beweisschicht (Hash, Zeitstempel, Screenshot-Bindung), Zeitachsen-Diff |

Gemeinsam heute: Stack und `capture.json` festzurren, danach arbeitet jeder gegen die Datei.

### Recht

| | Paket 1 (Regeln) | Paket 2 (20 Seiten) | Paket 3 |
|---|---|---|---|
| **Person A** *(sicherer im UWG)* | **DP-003** Zeitdruck — Schwarze Liste, unser Kernmuster | 10 Seiten **inkl. Branche je Seite** | Formulierungsrichtlinie, Haftungsabsicherung, Zulässigkeit der Abrufe |
| **Person B** | **DP-004** Kündigungsbutton + **DP-005a** Preisangabe/MwSt | 10 Seiten **inkl. Branche je Seite** | Dreistufenmodell begründen, „Consent or Pay"-Fundstelle, 3 Folien |

**Zwei Änderungen gegenüber gestern, bitte beachten:**

1. Jede Regel bekommt zusätzlich das Feld **`kategorie`** — genau einer der vier Werte `Zeitdruck` / `Zwang` / `Hindernisse` / `Irreführung`. Steht schon in [`_VORLAGE.yaml`](../rules/_VORLAGE.yaml).
2. Im Gold Standard kommt eine Spalte **`branche`** dazu (Ticketing, Reise, Mode, Telekommunikation, Möbel …). Ohne sie gibt es keine Statistik nach Branche — und die hat die Verbraucherzentrale ausdrücklich verlangt.

---

## 7. Tagesplan

### Mi 19.08. — Restabend

| | Aufgabe | Fertig heißt |
|---|---|---|
| Technik | **Technik-Kickoff** nach [`AGENDA_Technik.md`](AGENDA_Technik.md): Stack + `capture.json` festlegen | beides steht schriftlich im Repo |
| Technik | Playwright läuft, Screenshot + HTML von **viagogo**, **ein** Signal end-to-end | eine echte `capture.json` liegt vor |
| Recht | Briefing §2, 3, 5, 6 · `rules/README.md` · DP-001/002 als Muster · `bearbeiter` und `status: IN_ARBEIT` eintragen | eigene Regel ist zugeordnet und geöffnet |

### Do 20.08.

| | Aufgabe |
|---|---|
| Karthik | Pfadabarbeitung (Startseite → Produktdetail) · Signale für DP-001–004 · viagogo vollständig erfasst |
| Donghyun | Regel-Engine: YAML laden, Bedingungen auswerten, `unklar` bei fehlendem Signal · erste Tabellenausgabe |
| Recht | **Paket 1 fällig, 18:00** — DP-003, DP-004, DP-005a auf `REVIEW`, alle mit `kategorie` |
| Abends | **Walking Skeleton steht:** viagogo → Erfassung → eine Regel → eine Zeile in der Tabelle → PDF. Hier bricht garantiert etwas |

### Fr 21.08.

| | Aufgabe |
|---|---|
| Karthik | Countdown-Nachweis mit zwei Erfassungen und sauberem Kontext · Netzwerkmitschnitt vor Einwilligung · MwSt-Erkennung |
| Donghyun | **Beweisakte fertig** als PDF: Screenshot, Hash, Zeitstempel, Norm, Anspruchskette |
| Recht | **Paket 2 fällig, 18:00** — 20 Seiten, davon rund die Hälfte unauffällig, jeweils mit Branche |
| Nachmittags | System gegen Mensch. **Die Fehlalarmquote ist die wichtigere Zahl** |

### Sa 22.08.

| | Aufgabe |
|---|---|
| Technik | **Marktübersicht**: Filter nach Branche/Kategorie/Norm, Statistiken, CSV-Export · Zeitachsen-Diff zweier Erfassungen |
| Recht | **Paket 3 fällig** — Formulierungsrichtlinie, Disclaimer, Zulässigkeit der Abrufe, „Consent or Pay", 3 Folien |
| **23:00** | **Feature Freeze.** Danach nur noch Fehlerbehebung. Ausnahmslos |

### So 23.08.

Fehlerbehebung · Demo-Video aufnehmen · online erreichbare Fassung · **nur wenn alles steht:** Chrome-Extension aus `extractors.js` · Präsentation ausformulieren · 3× komplett durchsprechen.

### Mo 24.08. — Übergabetag, kein Entwicklungstag

> **Jedes Teammitglied kann die Demo allein vorführen und die zehn wahrscheinlichsten Rückfragen beantworten.**

Wir testen genau das: **eine Person aus dem juristischen Team führt die Demo allein vor.** Wo es hakt, wird dokumentiert, nicht wegerklärt. Absicherung, weil ab Dienstag keine Entwicklung da ist: Video **und** Online-Fassung.

### Di 25. / Mi 26.08.
Entwicklung nicht verfügbar. Juristisches Team schleift die Präsentation.

### Do 27.08. — Präsentation

---

## 8. Risiken

| Risiko | Gegenmaßnahme | Bis wann |
|---|---|---|
| ~~Keine Seite mit den gesuchten Mustern~~ | **erledigt** — die Verbraucherzentrale hat viagogo selbst genannt | ✅ |
| **Pfadabarbeitung auf viagogo scheitert** (Bot-Erkennung, wechselnde Selektoren) — dann fehlt uns der Referenzfall | zwei Ersatzseiten aus derselben Branche früh mit erfassen; Selektoren je Ziel in `targets/*.yaml`, nicht im Code | Do 20.08. |
| **Montag-Übergabe misslingt** — ab Dienstag keine Entwicklung | Video + Online-Fassung + Probelauf durch eine Person aus dem Recht | Mo 24.08. |
| **Regelwerk kommt zu spät** — die Engine hat nichts auszuführen | DP-003/004/005a vor DP-005b/006; früh auf `REVIEW` statt spät auf `FERTIG` | Do 20.08. |
| **Zu viele Fehlalarme** — macht uns selbst angreifbar (§ 4 Nr. 1, Nr. 2 UWG) | halber Gold Standard aus unauffälligen Seiten; „Pur-Abo" wird bewusst nicht beanstandet; im Zweifel eine Stufe herunter | Fr 21.08. |
| **Scope-Ausweitung** | Feature Freeze Sa 23:00, Ideen nach [`IDEAS.md`](IDEAS.md) | Sa 22.08. |
