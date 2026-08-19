# Strategie und Tagesplan

**Stand: 19.08.2026** · Entwicklungszeit bis **Mo 24.08.** · Präsentation **Do 27.08.**
Team: 2× Entwicklung (Donghyun, Karthik) · 2× Recht (Sebastian, +1)

---

## 1. Die Marktlücke — und warum sie unsere These schärft

Aus dem Seminar der Verbraucherzentrale Bayern (19.08.): Die bestehenden Werkzeuge werden **nicht wegen fehlender Funktionen nicht eingesetzt, sondern weil sie nicht ins Budget passen.**

Das ist die entscheidende Information dieser Woche. Wir lösen kein Erkennungsproblem — das ist gelöst. Wir lösen ein **Zugänglichkeitsproblem**.

### Was es schon gibt

| Angebot | Was es ist | Warum es für eine VZ nicht taugt |
|---|---|---|
| **FairPatterns** (Paris) | SaaS + Beratung, Figma-Plugin, KI-Agent. Kunden: HP, Wolters Kluwer, Bird & Bird | Enterprise-Preismodell, kein öffentlicher Preis, Angebot nur auf Anfrage. Liefert **Design-Empfehlungen und Risikobewertung** — keine Beweisdokumentation für die Durchsetzung. Adressat sind Unternehmen, die sich absichern wollen, nicht Stellen, die durchsetzen wollen |
| **R Systems** | kommerzielles Enterprise-Angebot eines IT-Dienstleisters | Preis auf Anfrage, Projektgeschäft. Gleiche Adressatenrichtung |
| **UIGuard** ([arXiv 2308.05898v2](https://arxiv.org/html/2308.05898v2)) | Forschungsprototyp: Computer Vision + NLP auf **Mobile Apps**, Taxonomie nach Gray et al. (5 Strategien, 14 Typen), Precision 0,83 / Recall 0,82 auf 6.352 UIs | Kein Produkt, kein Web, kein Recht. ML-basiert — Befunde sind **nicht reproduzierbar und nicht begründbar** |
| **rajnish159/Dark-Pattern-Detection** | regelbasierte Browser-Extension, JavaScript | 1 Stern, 3 Commits, unfertig. **Keine Lizenzangabe → Code rechtlich nicht nachnutzbar** (Urheberrecht gilt ohne Lizenz vollumfänglich). Reine Klassifikation, keine juristische Einordnung |

### Was keines davon tut

**Keines** erzeugt eine Dokumentation, die eine Verbraucherzentrale einer **Abmahnung beilegen** könnte. Alle sagen „hier ist ein Dark Pattern". Keines sagt „hier ist der gemessene Wert, hier die Norm, hier der Zeitstempel, hier der Hash — und das ist am 14.08. noch anders gewesen".

### Unsere Kernthese — geschärft

> **„Dark Patterns zu erkennen können andere längst. Sie bezahlbar und abmahnfähig zu dokumentieren kann niemand."**

Drei Belege in der Präsentation:

1. **Bezahlbar** — Open Source, selbst betreibbar, keine Lizenzkosten. Läuft auf einem Laptop der Verbraucherzentrale.
2. **Abmahnfähig** — Ausgabe ist eine Prüftabelle mit Norm, gemessenem Wert, Screenshot, Hash und Zeitstempel. Kein Werturteil, sondern Tatsachenfeststellung.
3. **Zeitachse** — wir erkennen, wenn ein Unternehmen ein Design still wieder einführt. Direkter Anschluss an die Durchsetzung von Unterlassungserklärungen.

---

## 2. Das zentrale Produkt: die Prüftabelle

Die VZ hat es im Seminar selbst gesagt: gebraucht wird **eine Tabelle**, aus der sich die Rechtsgrundlagen für eine Abmahnung entnehmen lassen.

**Damit ist die Tabelle nicht das letzte Feature, sondern das erste.** Sie ist der Demo-Mittelpunkt und wird bis Freitag gebaut, nicht bis Sonntag.

### Zielausgabe — Anlage zur Abmahnung

| Nr. | Befund | Gemessener Wert | Norm | Stufe | Nachweis |
|---|---|---|---|---|---|
| 1 | Ablehnung erfordert mehr Interaktionsschritte als Zustimmung | `reject_click_depth = 3` (Zustimmung: 1) | Art. 7 Abs. 4, Art. 4 Nr. 11 DSGVO | eindeutig | S-01.png · `sha256:a1b2…` · 19.08.2026 14:22:03 |
| 2 | Countdown springt nach Löschen aller Browserdaten auf denselben Startwert | `countdown_resets_on_revisit = true`, Startwert 900 s | Anh. zu § 3 Abs. 3 UWG Nr. 7 | eindeutig | S-02.png, S-03.png · 2 Messungen |
| 3 | Bestellbutton ohne gesetzliche Kennzeichnung | `order_button_label = "Jetzt bestellen"` | § 312j Abs. 3 BGB | eindeutig | S-04.png |

Darunter: Anspruchskette, Formulierungsrichtlinie, Haftungshinweis — alles aus dem Regelwerk, nichts frei formuliert.

---

## 3. Fünf Produktentscheidungen

### 3.1 Headless zuerst, Chrome-Erweiterung als Aufsatz

Der Vorschlag aus dem Team, das Ganze als Chrome-Plugin zu bauen, ist für die **Verbreitung** richtig — für den **Kern** aber nicht. Begründung:

| Anforderung | Headless (Playwright) | Extension |
|---|---|---|
| `countdown_resets_on_revisit` — sauberer Browserzustand | ein Aufruf: neuer Kontext | Nutzer muss Browserdaten löschen |
| `third_party_cookies_before_consent` | Netzwerk vor jeder Interaktion mitlesen | technisch möglich, unzuverlässig |
| 20 Seiten für den Gold Standard | Batchlauf | 20× von Hand |
| **Änderungen über Zeit dokumentieren** — von der Challenge ausdrücklich verlangt | geplanter Lauf ohne Menschen | nur wenn jemand die Seite besucht |

Eine Extension allein kann den Kern der Challenge — das **Monitoring** — nicht erfüllen.

**Der Kniff, mit dem wir beides bekommen:** Alle Signalmessungen werden als **reines Browser-JavaScript ohne Playwright-Abhängigkeit** geschrieben (`src/signals/extractors.js`). Playwright führt sie über `page.evaluate()` aus. Dieselbe Datei läuft unverändert als Content Script einer Extension. Die Extension kostet dann nur noch Manifest + Popup — ein Sonntagnachmittag, wenn wir vorne liegen. Liegen wir hinten, entfällt sie ohne Verlust.

### 3.2 Vier Muster statt sechs

DP-001, DP-002, DP-003, DP-004 werden fertig. DP-005 und DP-006 nur, wenn am Samstag Zeit bleibt.

Begründung: DP-002 und DP-004 sind reine Vorhandenseinsprüfungen mit nahezu null Fehlerquote. DP-003 ist unser stärkstes Argument überhaupt. DP-001 ist visuell am eindrucksvollsten. DP-005 setzt voraus, dass wir bis zum Bestellabschluss navigieren können — das gelingt nicht zuverlässig und kostet einen ganzen Tag.

**Vier belastbare Muster schlagen sechs wacklige.** Das gilt in der Präsentation genauso wie im Code.

### 3.3 Kein Code aus rajnish159 übernehmen

Das Repository hat **keine Lizenzangabe**. Ohne Lizenz gilt das Urheberrecht vollumfänglich — eine Nachnutzung wäre unzulässig. Wir sehen es uns 30 Minuten als Ideengeber an und schreiben alles selbst.

*Für die Präsentation ist das sogar ein Pluspunkt: Ein Team, das die Lizenzlage eines fremden Repos prüft, bevor es Code übernimmt, ist genau das Team, dem man eine Rechtsanwendung zutraut.*

### 3.4 Kein Machine Learning im Befund

Unverändert gegenüber dem Briefing — und durch UIGuard bestätigt: Precision 0,83 heißt, dass **jeder sechste Befund falsch** ist. Für eine Verbraucherzentrale, die daraus eine Abmahnung baut, ist das unbrauchbar. Unsere Regeln sind deterministisch: gleiche Eingabe, gleiches Ergebnis, jederzeit nachvollziehbar.

UIGuard nennen wir in der Präsentation als Stand der Forschung — und als Beleg dafür, dass wir die Alternative kennen und bewusst anders entschieden haben.

### 3.5 Keine Datenbank

Ein Erfassungslauf = eine JSON-Datei + Screenshots unter `data/captures/<domain>/<zeitstempel>/`. Die Zeitachse ist ein Vergleich zweier JSON-Dateien. Das ist in zwei Stunden gebaut, mit bloßem Auge prüfbar und am Montag von jedem im Team zu bedienen.

---

## 4. Architektur und die technische Schnittstelle

```
              capture.json
                   ▲
   schreibt        │        liest
   Karthik         │        Donghyun
   (Erfassung)     │        (Regelwerk + Bericht)
```

Zwischen Recht und Technik steht `rules/*.yaml`. Zwischen den beiden Entwicklern steht `capture.json`. **Beide Schnittstellen werden heute festgelegt und danach nicht mehr angefasst** — dann blockiert niemand niemanden.

```jsonc
{
  "meta": {
    "url": "https://beispielshop.de/produkt/123",
    "timestamp": "2026-08-19T14:22:03+02:00",
    "capture_mode": "headless",
    "viewport": { "width": 1440, "height": 900 },
    "user_agent": "...",
    "dom_hash": "sha256:a1b2c3...",
    "run_id": "2026-08-19T14-22-03_beispielshop-de"
  },
  "artifacts": {
    "screenshot": "S-01.png",
    "html": "page.html"
  },
  "signals": {
    "banner_detected": true,
    "accept_button_area_px2": 12480,
    "reject_button_area_px2": 4100,
    "reject_click_depth": 3,
    "order_button_label": "Jetzt bestellen"
  },
  "signal_errors": {
    "price_at_checkout": "Bestellabschluss nicht erreichbar"
  }
}
```

**Die wichtigste Regel dieser Datei:** Was nicht gemessen werden konnte, steht **nicht** in `signals`, sondern mit Begründung in `signal_errors`. Die Regel-Engine setzt jede Regel, die ein fehlendes Signal braucht, automatisch auf `unklar`. So entsteht die dritte Stufe technisch von selbst — genau wie im Briefing beschrieben.

### Stack

Node + TypeScript + Playwright (Chromium), `js-yaml` fürs Regelwerk, HTML-Bericht → PDF über Playwright (schon vorhanden). Kein `eval()` für die Bedingungen — ein kleiner eigener Vergleichsparser für `> < >= <= == != and`.

Begründung für JavaScript statt Python: Die Signalmessung ist DOM- und CSS-Arbeit und muss ohnehin im Browser laufen. Mit JS gibt es keine Sprachgrenze zwischen Messung, Extension und Bericht.

---

## 5. Aufgabenteilung

### Entwicklung

| | Verantwortlich für | Warum |
|---|---|---|
| **Karthik** | Erfassungsschicht: Playwright-Steuerung, `extractors.js`, Netzwerkmitschnitt, Screenshots, `capture.json` schreiben | In sich geschlossen, gut parallelisierbar, und es ist genau der Code, der später zur Extension wird |
| **Donghyun** | Regel-Engine (YAML laden, Bedingungen auswerten), Prüftabelle, Beweisschicht (Hash, Zeitstempel, Screenshot-Bindung), Zeitachsen-Diff | Trägt die gesamte Argumentation der Präsentation — und muss am Montag von einem Nicht-Entwickler bedienbar sein |

Gemeinsam heute: `capture.json` festzurren. Danach arbeitet jeder gegen die Datei, nicht gegen den anderen.

### Recht

| | Paket 1 (Regeln) | Paket 2 (Gold Standard) | Paket 3 |
|---|---|---|---|
| **Person A** *(stärker im Lauterkeitsrecht)* | **DP-003** Dringlichkeit — unser Kernmuster, Schwarze Liste | 10 Seiten | Formulierungsrichtlinie + Haftungsabsicherung |
| **Person B** | **DP-004** Kündigungsbutton — einfachster Einstieg | 10 Seiten | Begründung Dreistufenmodell + 3 Folien |

DP-001 und DP-002 sind aus dem Kickoff fertig. DP-005/DP-006 nur bei Restzeit — **niemand fängt damit an, bevor DP-003 und DP-004 auf `REVIEW` stehen.**

Bitte selbst zuordnen, wer A und wer B ist: DP-003 gehört zu der Person, die sich im UWG sicherer fühlt.

---

## 6. Tagesplan

### Mi 19.08. — heute, Restabend

| | Aufgabe | Fertig heißt |
|---|---|---|
| Technik | Stack aufsetzen, `capture.json` festlegen, Playwright startet und macht Screenshot + HTML einer Seite. **Ein** Signal end-to-end: `has_kuendigungsbutton` | `npm start -- https://beispiel.de` erzeugt eine `capture.json` mit einem echten Signal |
| Technik | **3 Kandidatenseiten mit zurücksetzendem Countdown suchen und festhalten** | in `data/gold-standard/kandidaten.md` notiert |
| Recht | Briefing §2, 3, 5, 6 lesen · `rules/README.md` lesen · DP-001 und DP-002 als Muster durchgehen · `bearbeiter` + `status: IN_ARBEIT` eintragen | eigene Regel ist zugeordnet und geöffnet |

> ⚠️ Die Countdown-Suche ist heute Abend wichtiger als jede Codezeile. **Unser stärkstes Demo-Argument braucht eine Seite, die es tatsächlich tut.** Finden wir keine, müssen wir die Demo umbauen — und das wollen wir am Mittwoch wissen, nicht am Samstag.

### Do 20.08.

| | Aufgabe |
|---|---|
| Karthik | Signale für DP-001–004: Buttonflächen, Kontraste, Klicktiefe, Buttonbeschriftungen, Countdown-Erkennung |
| Donghyun | Regel-Engine: YAML laden, Bedingungen auswerten, `unklar` bei fehlendem Signal, erste Textausgabe |
| Recht | **Paket 1 fällig, 18:00** — DP-003 und DP-004 auf `REVIEW` |
| Abends | Erster Gesamtlauf: alle Regeln durchs System. **Hier bricht garantiert etwas** — Zeitpuffer ist eingeplant |

### Fr 21.08.

| | Aufgabe |
|---|---|
| Karthik | Countdown-Nachweis: zwei Erfassungen mit sauberem Kontext, Vergleich · Netzwerkmitschnitt vor Einwilligung |
| Donghyun | **Prüftabelle** als HTML + PDF, mit Hash, Zeitstempel, Screenshot-Verweis |
| Recht | **Paket 2 fällig, 18:00** — 20 Seiten von Hand bewertet, davon rund die Hälfte unauffällig |
| Nachmittags | System gegen Mensch: erste Trefferzahlen. **Fehlalarmquote ist die wichtigere Zahl** |

### Sa 22.08.

| | Aufgabe |
|---|---|
| Technik | Zeitachse: zwei Erfassungen derselben Seite vergleichen, Änderungen ausweisen · Bericht aufräumen |
| Recht | **Paket 3 fällig** — Formulierungsrichtlinie, Disclaimer, Begründung Dreistufenmodell, 3 Folien |
| **23:00** | **Feature Freeze.** Danach nur noch Fehlerbehebung. Ausnahmslos |

### So 23.08.

| | Aufgabe |
|---|---|
| Technik | Fehlerbehebung · Demo-Video aufnehmen · Online erreichbare Fassung · **nur wenn alles steht: Chrome-Extension** aus `extractors.js` |
| Alle | Präsentation ausformulieren · 3× komplett durchsprechen |

### Mo 24.08. — Übergabetag, nicht Entwicklungstag

Am Ende dieses Tages muss dieser Satz wahr sein:

> **Jedes Teammitglied kann die Demo allein von Anfang bis Ende vorführen und die zehn wahrscheinlichsten Rückfragen beantworten.**

Wir testen genau das: **eine Person aus dem juristischen Team führt die Demo allein vor.** Wo es hakt, wird dokumentiert — nicht wegerklärt.

Absicherung, weil ab Dienstag keine Entwicklung mehr da ist: aufgezeichnetes Video **und** online erreichbare Fassung. Die Präsentation darf nicht von einem bestimmten Laptop abhängen.

### Di 25. / Mi 26.08.
Entwicklung nicht verfügbar. Juristisches Team schleift die Präsentation.

### Do 27.08. — Präsentation

---

## 7. Risiken

| Risiko | Gegenmaßnahme | Bis wann |
|---|---|---|
| **Keine Seite mit zurücksetzendem Countdown gefunden** — unser stärkstes Argument hätte kein Anschauungsobjekt | heute Abend 3 Kandidaten suchen und festhalten | **Mi 19.08.** |
| **Montag-Übergabe misslingt** — ab Dienstag ist keine Entwicklung da | Demo-Video + Online-Fassung + Probelauf durch eine Person aus dem Recht | Mo 24.08. |
| **Regelwerk kommt zu spät** — die Engine hat nichts auszuführen | DP-003/004 haben Vorrang vor DP-005/006; früh auf `REVIEW` statt spät auf `FERTIG` | Do 20.08. |
| **Zu viele Fehlalarme** — ein System, das überall Verstöße sieht, ist wertlos und macht uns angreifbar (§ 4 Nr. 1, Nr. 2 UWG) | die Hälfte des Gold Standards sind unauffällige Seiten; im Zweifel eine Stufe herunter | Fr 21.08. |
| **Scope-Ausweitung** | Feature Freeze Sa 23:00, Ideen nach `docs/IDEAS.md` | Sa 22.08. |
