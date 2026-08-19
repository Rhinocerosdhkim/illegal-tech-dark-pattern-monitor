# Regelwerk – Anleitung für das juristische Team

**Frist: Donnerstag, 20.08., 18:00 Uhr** · Legal Loves Tech 2026 · Challenge VZ (III)

---

## Worum es geht

Die Dateien in diesem Ordner sind **nicht Dokumentation, sondern Produktlogik**. Unser System liest sie beim Start ein und wendet sie unmittelbar an. Was ihr hier schreibt, ist das, was das System später bewertet und in den Bericht schreibt.

Ihr müsst **kein YAML können**. Es ist eine Liste von Feldern mit Doppelpunkt. Wenn ihr euch an die Vorlage haltet, funktioniert es. Bei Formatfehlern: einfach im Entwicklungsteam melden, das ist in zwei Minuten behoben.

---

## Dateien in diesem Ordner

| Datei | Was es ist |
|---|---|
| `README.md` | dieses Dokument |
| `_SIGNALE.md` | **Liste aller messbaren Signale.** Nur daraus dürft ihr wählen |
| `_VORLAGE.yaml` | leere Vorlage mit Erklärungen zu jedem Feld |
| `DP-001_Consent-Buttons.yaml` | ✅ **fertiges Beispiel** – als Muster lesen |
| `DP-002_Button-Loesung.yaml` | ✅ **fertiges Beispiel** – als Muster lesen |
| `DP-003_Dringlichkeit.yaml` | 🟡 Entwurf – **von euch zu vervollständigen** |
| `DP-004_Kuendigungsbutton.yaml` | 🟡 Entwurf – **von euch zu vervollständigen** |
| `DP-005_Drip-Pricing.yaml` | 🟡 Entwurf – **von euch zu vervollständigen** |
| `DP-006_Informationsverdeckung.yaml` | 🟡 Entwurf – **von euch zu vervollständigen** |

Die beiden fertigen Beispiele haben wir im Kickoff gemeinsam erarbeitet. Sie zeigen den Zielzustand. Die vier Entwürfe enthalten bereits Vorschläge für Normen und offene Fragen – prüft diese kritisch, sie sind von Nicht-Juristen vorbereitet und können falsch sein.

---

## Die drei Regeln

### 1. `signals` nur aus `_SIGNALE.md`

Das System kann ausschließlich messen, was in dieser Liste steht. Ein Signal wie `nutzer_fuehlt_sich_unter_druck_gesetzt` gibt es nicht und wird es bis Sonntag nicht geben.

Wenn ihr ein Signal braucht, das fehlt: **fragt zuerst**, bevor ihr die Regel darauf aufbaut. Manches ist in einem Tag machbar, manches nicht.

### 2. Jede Bedingung braucht eine Zahl oder ein Ja/Nein

| ❌ unbrauchbar | ✅ brauchbar |
|---|---|
| „unangemessen groß" | `accept_button_area_px2 / reject_button_area_px2 > 2.0` |
| „schwer auffindbar" | `kuendigungsbutton_click_depth > 2` |
| „nicht hinreichend deutlich" | `font_size_min_px < 10` |

Wenn ihr für eine Zahl **keine** Grundlage in Rechtsprechung, Leitlinien oder Literatur findet: schreibt das offen ins Feld `threshold_source`. Zum Beispiel:

```yaml
threshold_source: >
  Keine Rechtsprechungsgrundlage ersichtlich. Eigene Festlegung des Teams.
  Faktor 2,0 bewusst konservativ gewählt, um Fehlalarme zu vermeiden.
```

**Das ist völlig in Ordnung und wird uns in der Präsentation nicht schaden – im Gegenteil.** Ein Team, das offenlegt, wo es eigene Annahmen trifft, wirkt souveräner als eines, das so tut, als sei alles judiziert. Was uns schaden würde, wäre eine erfundene Fundstelle.

### 3. `eindeutig` ist die Ausnahme, nicht die Regel

Faustregel: In `eindeutig` gehört nur, was ihr **vor Gericht ohne Wertungsspielraum vertreten** würdet.

- Schwarze Liste (Anhang zu § 3 Abs. 3 UWG) → oft `eindeutig`, weil per se unlauter
- Fehlender Pflichthinweis / fehlendes Pflichtelement → oft `eindeutig`, weil reine Tatsachenfeststellung
- Alles, was von „durchschnittlicher Verbraucher", „Spürbarkeit", „Gesamteindruck" abhängt → **höchstens** `verdaechtig`

Im Zweifel eine Stufe herunter. Ein vorsichtiges System ist für eine Verbraucherzentrale brauchbar; ein übertreibendes ist es nicht – und kann uns selbst angreifbar machen (§ 4 Nr. 1, Nr. 2 UWG).

---

## Was bedeutet eigentlich welche Stufe?

| Stufe | Bedeutung | Sprachliche Umsetzung im Bericht |
|---|---|---|
| `eindeutig` | Tatbestand nach unserer Prüfung erfüllt, kein ernsthafter Wertungsspielraum | „Prüfhinweis mit hoher Auffälligkeit" |
| `verdaechtig` | belastbarer Anhaltspunkt, aber Auslegung möglich | „Verdachtsmoment" |
| `unklar` | Merkmal maschinell nicht feststellbar, Prüfung durch Menschen nötig | „Manuelle Prüfung erforderlich" |
| `unauffällig` | keine Bedingung erfüllt | – |

> Das Wort **„Verstoß"** verwenden wir im Systemoutput bewusst nicht als Feststellung. Die endgültige Formulierungsrichtlinie kommt aus Paket 3 – bis dahin gilt obige Spalte als Arbeitsstand.

`unklar` müsst ihr nicht selbst befüllen. Das System vergibt diese Stufe automatisch, wenn ein für die Regel benötigtes Signal nicht erhoben werden konnte (z. B. Banner nicht gefunden, Seite nicht erreichbar). **Diese Stufe ist ein Qualitätsmerkmal, kein Fehler.**

---

## Arbeitsteilung

| Regel | Bearbeiter:in | Bemerkung |
|---|---|---|
| DP-001 | *(gemeinsam im Kickoff)* | fertig, als Muster |
| DP-002 | *(gemeinsam im Kickoff)* | fertig, als Muster |
| DP-003 | ................ | Schwarze Liste, gut machbar |
| DP-004 | ................ | einfachste Regel, guter Einstieg |
| DP-005 | ................ | mehrere Normebenen, mittel |
| DP-006 | ................ | **schwerste Regel** – an die Person mit der meisten Sicherheit im Lauterkeitsrecht |

**Wenn die Zeit knapp wird:** lieber vier saubere Regeln als sechs halbfertige. Sagt früh Bescheid, dann priorisieren wir gemeinsam. DP-005 und DP-006 sind die Kandidaten, die zuerst entfallen.

---

## Ablauf

1. Regel öffnen, `bearbeiter` und `status: IN_ARBEIT` eintragen
2. Felder ausfüllen, `offene_fragen` nutzen für alles, was ihr nicht klären könnt
3. `status: REVIEW` setzen und im Teamchat melden
4. Entwicklungsteam lädt die Regel ins System und meldet zurück, ob sie technisch funktioniert
5. Nach gemeinsamer Durchsicht: `status: FERTIG`

**Wichtig:** Schickt Regeln lieber früh im Zustand `REVIEW` als spät im Zustand `FERTIG`. Wir müssen am Donnerstagabend erstmals alle Regeln durch das System jagen – da wird garantiert etwas brechen, und dafür brauchen wir Zeit.

---

## Häufige Fragen

**„Ich bin mir bei der Norm nicht sicher."**
Trag sie mit einem Fragezeichen in `offene_fragen` ein. Eine unsichere Norm ist besser als keine – wir klären sie gemeinsam.

**„Mein Muster passt unter mehrere Normen."**
Gut. Trag alle in `legal_basis` ein und gib in `anspruchskette` an, welche davon die praktisch durchsetzbare ist. Für eine Verbraucherzentrale ist das meist der Weg über § 8 UWG.

**„Kann ich einen Wert später noch ändern?"**
Ja, jederzeit. Das ist genau der Grund, warum das Regelwerk vom Code getrennt ist: ihr könnt Schwellenwerte anpassen, ohne dass jemand programmieren muss. Am Freitagabend werden wir genau das tun, wenn wir unsere Ergebnisse mit dem Gold Standard vergleichen.

**„Muss das auf Deutsch sein?"**
Ja – Berichte und Präsentation sind auf Deutsch. Die Feldnamen sind englisch, die Inhalte deutsch. Wer sich auf Englisch wohler fühlt: schreibt englisch und markiert es, wir übersetzen am Samstag.

---

## For English speakers – short version

These YAML files **are the product logic**, not documentation. The system reads them directly.

Three rules when filling them in:

1. **`signals` may only contain entries from `_SIGNALE.md`.** That list is everything the system can technically measure. Need something else? Ask first.
2. **Every condition needs a number or a yes/no.** "Inappropriately large" is unusable; `ratio > 2.0` is usable. If there is no case law backing your threshold, say so honestly in `threshold_source` — that is fine and we will state it openly in the presentation. Inventing a citation is not fine.
3. **`eindeutig` (clear-cut) is the exception.** Only for things you would defend in court with no room for interpretation — typically per-se prohibitions from the UWG blacklist, or the plain absence of a mandatory element. Anything depending on "the average consumer" or an overall impression goes to `verdaechtig` at most. When in doubt, go one level down.

Field names are English, content is German (reports and presentation are in German). If you prefer to draft in English, do so and mark it — we will translate on Saturday.

Read `DP-001` and `DP-002` first as worked examples, then complete your assigned rule. Deadline **Thursday 18:00**. Send it in `status: REVIEW` early rather than `FERTIG` late.
