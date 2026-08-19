# Projekt-Briefing: Dark-Pattern- und Design-Monitor

**Legal Loves Tech Hackathon 2026 · Challenge VZ (III) · Verbraucherzentrale Bayern**

Version 1.0 · Stand: 19.08.2026 · Zielgruppe: gesamtes Team, insbesondere die juristischen Teammitglieder

---

## 1. Warum dieses Dokument existiert

In unserem Team arbeiten Jurist:innen und Entwickler:innen zusammen. Beide Seiten sprechen unterschiedliche Sprachen, und die Zeit ist knapp. Dieses Dokument soll sicherstellen, dass alle dasselbe Produkt vor Augen haben und dass jede Person genau weiß, **was sie bis wann in welchem Format abliefert**.

Bitte lest mindestens die Abschnitte 2, 3, 5 und 6 vollständig. Diese vier Abschnitte enthalten alles, was für die juristische Arbeit unmittelbar relevant ist.

---

## 2. Was wir bauen – und was wir bewusst *nicht* bauen

### 2.1 Die Aufgabenstellung

Die Challenge verlangt einen **Webseiten- und Design-Monitor**, der digitale Oberflächen analysiert, Dark Patterns erkennt, Änderungen dokumentiert, auffällige Gestaltungsmuster klassifiziert und die Ergebnisse für die **juristische Prüfung, Marktbeobachtung und Verbraucherinformation** aufbereitet.

Entscheidend ist ein Blick auf die genannten möglichen Nutzer: Verbraucherzentralen und -verbände, Mitbewerber, Wettbewerbsverbände, IHK und Handwerkskammern, Datenschutzaufsichtsbehörden, die Bundesnetzagentur als Digital Services Koordinator.

**Das sind ausschließlich juristische Akteure – keine Verbraucher:innen.** Diese Akteure brauchen kein Tool, das ihnen sagt „diese Seite ist böse". Sie brauchen ein Tool, das ihnen die Arbeit abnimmt, einen Verstoß **belastbar zu dokumentieren**.

### 2.2 Unsere Kernthese

> **Dark Patterns zu erkennen ist einfach. Schwierig ist es, sie so zu dokumentieren, dass sie rechtlich verwertbar sind.**

Daraus folgt unsere Produktdefinition:

> Unser System ist **kein KI-Richter**, der entscheidet, ob ein Verstoß vorliegt. Es ist ein **Beweiserhebungs- und Strukturierungswerkzeug**, das einer Juristin oder einem Juristen die Tatsachengrundlage so aufbereitet, dass sie oder er die rechtliche Subsumtion vornehmen kann.

### 2.3 Das Anti-Muster (was andere Teams machen werden)

Sehr wahrscheinlich werden mehrere Teams Folgendes bauen:

> Screenshot einer Webseite → an ein Sprachmodell schicken → „Finde Dark Patterns" → Ausgabe einer Liste

Das ist in 30 Minuten gebaut und scheitert aus vier Gründen:

1. **Nicht reproduzierbar.** Zweimal derselbe Input, zweimal ein anderes Ergebnis.
2. **Nicht begründbar.** Auf die Frage „Woraus ergibt sich das?" lautet die Antwort „das Modell hat es gesagt". Das ist vor Gericht wertlos.
3. **Keine Zeitachse.** Die Challenge verlangt ausdrücklich, *Änderungen zu dokumentieren*. Ein Einmal-Scan kann das nicht.
4. **Rechtlich riskant.** Eine falsch behauptete Rechtsverletzung kann selbst rechtswidrig sein (dazu Abschnitt 6, Paket 3).

Wir gehen deshalb einen anderen Weg.

### 2.4 Unser Ansatz: Signale → Regelwerk → Bewertung

```
    Webseite
       │
       ▼
[1] ERFASSUNG            Screenshot, HTML, Barrierefreiheitsbaum,
                         Netzwerkverkehr, Zeitstempel
       │
       ▼
[2] SIGNALE              Messbare Fakten, rein technisch ermittelt:
                         Buttonfläche in px², Kontrastwerte, Klickanzahl,
                         Buttonbeschriftung, vorausgewählte Checkboxen ...
       │                 → deterministisch, jederzeit reproduzierbar
       ▼
[3] REGELWERK            ★ HIER ARBEITET DAS JURISTISCHE TEAM ★
                         Signale werden Tatbestandsmerkmalen zugeordnet.
                         Ergebnis: Norm + Bewertungsstufe
       │
       ▼
[4] BEWERTUNG            eindeutig / verdächtig / unklar / unauffällig
       │
       ▼
[5] ZEITACHSE            Vergleich mit früheren Erfassungen (Diff)
       │
       ▼
[6] BEWEISBERICHT        Screenshot + Prüfsumme + Zeitstempel + Norm
                         + nachvollziehbare Begründung
```

Ein Sprachmodell kommt nur an zwei eng begrenzten Stellen zum Einsatz: bei der sprachlichen Auslegung mehrdeutiger Formulierungen und bei der Formulierung der Berichtstexte. **Es trifft niemals die Bewertungsentscheidung.**

---

## 3. Die entscheidende Übersetzungsleistung

Dies ist die intellektuelle Kernaufgabe des Projekts – und sie ist juristisch, nicht technisch.

### 3.1 Jede Norm ist bereits eine Wenn-Dann-Struktur

Für die Entwickler:innen im Team, in ihrer Sprache formuliert:

| Juristischer Begriff | Entsprechung im Code |
|---|---|
| Tatbestand | die gesamte `if`-Bedingung |
| Tatbestandsmerkmal | eine einzelne Teilbedingung |
| Rechtsfolge | der `then`-Block |
| Subsumtion | das Einsetzen konkreter Tatsachen in die Bedingung |

Juristinnen und Juristen sind darin geübt, Normen in ihre Merkmale zu zerlegen. Genau diese Fähigkeit brauchen wir – nur schreiben wir das Ergebnis nicht in einen Gutachtentext, sondern in eine strukturierte Datei.

### 3.2 Die Leitfrage

Statt zu fragen „Liegt hier ein Verstoß vor?" stellen wir konsequent diese Frage:

> **„Welche Bedingungen müssen auf dem Bildschirm erfüllt sein, damit dieses Tatbestandsmerkmal bejaht werden kann – und lässt sich jede dieser Bedingungen allein anhand von Screenshot und HTML mit Ja/Nein oder einer Zahl beantworten?"**

### 3.3 Drei Prüffragen für jede Bedingung

Bevor eine Bedingung ins Regelwerk aufgenommen wird, muss sie alle drei Fragen bestehen:

1. **Maschinell beobachtbar?** Lässt sie sich allein aus Screenshot und HTML beantworten? Wenn dafür ein Vertragsdokument, ein Gespräch oder Wissen über interne Abläufe nötig wäre → nicht aufnehmen oder als „unklar" einstufen.
2. **Eindeutig entscheidbar?** Ja/Nein oder eine Zahl. Formulierungen wie „unangemessen", „hinreichend deutlich" oder „im Einzelfall" sind ohne konkreten Schwellenwert unbrauchbar.
3. **Rückverfolgbar?** Können wir bei Nachfrage die Bewertung bis zur Norm zurückführen?

### 3.4 Beispiel der Übersetzung

**Norm:** Art. 7 Abs. 4 i. V. m. Art. 4 Nr. 11 DSGVO – die Einwilligung muss freiwillig erteilt werden.

**Juristische Zwischenüberlegung:** Freiwilligkeit setzt voraus, dass die Ablehnung nicht spürbar erschwert ist gegenüber der Zustimmung (vgl. auch ErwG 32, 42).

**Übersetzung in messbare Signale:**

| Bedingung | Signal | Schwellenwert |
|---|---|---|
| Ablehnung erfordert mehr Interaktionsschritte | `reject_click_depth` | `> 1`, während Zustimmung mit einem Klick möglich ist |
| Zustimmungsbutton deutlich größer | `accept_button_area_px2 / reject_button_area_px2` | `> 2.0` |
| Ablehnung visuell zurückgesetzt | Differenz der Kontrastwerte | `> 3.0` |
| Vorausgewählte Einwilligungen | `preselected_checkbox_count` | `> 0` |

Genau diese Tabelle – für sechs Muster – ist unser Regelwerk.

---

## 4. Die Schnittstelle zwischen Recht und Technik: das Regelwerk

Damit beide Teilteams **parallel** arbeiten können, ohne aufeinander zu warten, gibt es genau eine verbindliche Schnittstelle: eine Regeldatei im YAML-Format.

```
              rules/*.yaml
                   ▲
   geschrieben vom │ gelesen vom
   juristischen    │ Entwicklungs-
   Team            │ team
```

**Diese Datei ist nicht Dokumentation. Sie ist die Produktlogik.** Was dort steht, wird vom System unmittelbar ausgeführt.

### 4.1 Aufbau einer Regel

```yaml
- id: DP-001
  name_de: "Ungleiche Gestaltung der Consent-Buttons"

  legal_basis:                    # Normen, so präzise wie möglich
    - "Art. 7 Abs. 4 DSGVO"
    - "Art. 4 Nr. 11 DSGVO"
    - "ErwG 32, 42 DSGVO"

  tatbestand_de: >                # ein bis zwei Sätze, laienverständlich
    Eine Einwilligung ist nur wirksam, wenn sie freiwillig erteilt wird.
    Freiwilligkeit setzt voraus, dass die Ablehnung nicht erschwert ist.

  signals:                        # NUR aus der Signal-Liste (Abschnitt 4.2)
    - accept_button_area_px2
    - reject_button_area_px2
    - reject_click_depth
    - accept_contrast_ratio
    - reject_contrast_ratio
    - preselected_checkbox_count

  verdict_rules:
    eindeutig:                    # kaum bestreitbar
      - "reject_click_depth > 1"
      - "accept_button_area_px2 / reject_button_area_px2 > 2.0"
    verdaechtig:                  # Anhaltspunkt, Auslegungsspielraum
      - "accept_contrast_ratio - reject_contrast_ratio > 3.0"
      - "preselected_checkbox_count > 0"
    # trifft nichts zu → automatisch "unauffällig"

  threshold_source: >             # Woher kommt der Schwellenwert?
    Eigene Festlegung des Teams, keine Rechtsprechungsgrundlage.
    Begründung: Faktor 2 als konservative Untergrenze gewählt.

  explanation_template_de: >      # erscheint wörtlich im Bericht
    Der Ablehnen-Button misst {reject_button_area_px2} px²,
    der Zustimmen-Button {accept_button_area_px2} px².
    Die Ablehnung erfordert {reject_click_depth} Interaktionsschritte.
    Dies begründet den Verdacht einer nicht freiwillig erteilten Einwilligung.

  disclaimer_required: true
```

### 4.2 Wichtigste Regel für die Befüllung

> **Das Feld `signals` darf ausschließlich Einträge aus der unten stehenden Liste enthalten.**

Diese Liste enthält alles, was unser System technisch messen kann. Wird ein Signal benötigt, das nicht enthalten ist, muss dies **vorher** mit dem Entwicklungsteam abgestimmt werden – möglicherweise ist es in der verfügbaren Zeit nicht umsetzbar.

**Verfügbare Signale:**

*Buttons und Bedienelemente*
- `accept_button_area_px2`, `reject_button_area_px2` – Fläche in Pixeln
- `accept_contrast_ratio`, `reject_contrast_ratio` – Kontrastverhältnis nach WCAG
- `reject_click_depth` – Anzahl der Interaktionsschritte bis zur vollständigen Ablehnung
- `button_label_text` – Beschriftung im Wortlaut
- `preselected_checkbox_count` – Anzahl vorausgewählter Auswahlfelder

*Texte und Hinweise*
- `has_zahlungspflichtig_label` – Ja/Nein
- `has_kuendigungsbutton` – Ja/Nein
- `countdown_element_present` – Ja/Nein
- `countdown_resets_on_revisit` – Ja/Nein (Prüfung durch erneuten Aufruf)
- `scarcity_text_present` – Ja/Nein (z. B. „nur noch 2 verfügbar")

*Preise*
- `price_listed`, `price_at_checkout`, `price_delta`

*Verdeckung von Informationen*
- `hidden_by_opacity_count`, `font_size_min_px`, `scroll_depth_of_required_info`

*Netzwerk*
- `third_party_cookies_before_consent` – Anzahl vor erteilter Einwilligung

---

## 5. Die sechs Muster im Bearbeitungsumfang

Wir bearbeiten bewusst **sechs** Muster gründlich statt zwanzig oberflächlich.

| ID | Muster | Rechtlicher Anknüpfungspunkt | Schwierigkeit |
|---|---|---|---|
| DP-001 | Ungleiche Consent-Buttons | Art. 7 Abs. 4, Art. 4 Nr. 11 DSGVO; ErwG 32, 42, 43 | mittel |
| DP-002 | Fehlende oder unklare Button-Lösung | § 312j Abs. 3, 4 BGB | gering, sehr eindeutig |
| DP-003 | Vorgetäuschte Dringlichkeit / Knappheit | Anhang zu § 3 Abs. 3 UWG (insb. Nr. 7); §§ 5, 5a UWG | gering bis mittel |
| DP-004 | Fehlender Kündigungsbutton | § 312k BGB | gering, sehr eindeutig |
| DP-005 | Versteckte Kosten / Drip Pricing | PAngV; §§ 5, 5a UWG | mittel |
| DP-006 | Verdeckung pflichtiger Informationen | §§ 5, 5a UWG; Art. 246a EGBGB i. V. m. § 312d BGB | hoch |

### Hinweise zu einzelnen Mustern

**DP-002 und DP-004** sind unsere zuverlässigsten Muster: Das Vorhandensein einer bestimmten Beschriftung bzw. eines bestimmten Bedienelements lässt sich technisch nahezu fehlerfrei feststellen. Beide eignen sich hervorragend für die Vorführung.

**DP-003**: Der eigentliche Nachweis liegt nicht darin, dass ein Countdown existiert, sondern darin, dass er **bei erneutem Aufruf zurückgesetzt** wird. Genau das können wir automatisiert nachweisen – und genau das ist der Anknüpfungspunkt zur Schwarzen Liste.

**Art. 25 DSA** haben wir bewusst *nicht* als eigenständiges Muster aufgenommen. Grund: Art. 25 Abs. 2 DSA nimmt Sachverhalte aus, die bereits von der UGP-Richtlinie (umgesetzt im UWG) oder der DSGVO erfasst sind. Eine eigenständige Feststellung eines DSA-Verstoßes wäre daher in vielen Fällen angreifbar. **Wir erwähnen Art. 25 DSA in der Präsentation als übergreifenden Rahmen und als Ausblick – aber nicht als Bewertungsgrundlage.** Wenn jemand aus dem juristischen Team diese Einschätzung fundiert widerlegen oder vertiefen möchte: sehr gerne, das wäre ein starker Punkt in der Fragerunde.

---

## 6. Arbeitspakete des juristischen Teams

Drei Pakete mit festen Fristen. Bitte behandelt die Fristen als verbindlich – das Entwicklungsteam ist davon unmittelbar abhängig.

---

### 📦 Paket 1 – Regelwerk

**Frist: Donnerstag, 20.08., 18:00 Uhr**

**Ergebnis:** Sechs vollständig ausgefüllte Regeln im oben beschriebenen Format.

**Vorgehen:**
- DP-001 und DP-002 erarbeiten wir gemeinsam im Kickoff-Workshop als Muster.
- DP-003 bis DP-006 werden im juristischen Team aufgeteilt (ein bis zwei Muster pro Person).
- DP-006 sollte die Person übernehmen, die sich im Lauterkeitsrecht am sichersten fühlt.

**Drei verbindliche Vorgaben:**

1. **Nur Signale aus der Liste in Abschnitt 4.2 verwenden.** Fehlt etwas: vorher fragen.
2. **Jede Bedingung braucht einen konkreten Wert.** „Unangemessen groß" ist unbrauchbar, „Faktor 2,0" ist brauchbar. Gibt es für den Wert eine Grundlage in Rechtsprechung, Leitlinien oder Literatur – bitte im Feld `threshold_source` angeben. Gibt es keine, schreibt ehrlich „eigene Festlegung des Teams". **Das ist völlig in Ordnung.** Wichtig ist allein die Transparenz; wir werden das in der Präsentation auch so benennen.
3. **In `eindeutig` gehört nur, was kaum bestreitbar ist.** Im Zweifel eine Stufe herabsetzen. Ein System, das vorsichtig bewertet, ist für Verbraucherzentralen weit brauchbarer als eines, das übertreibt.

**Falls die Zeit knapp wird:** Lieber vier saubere Regeln als sechs halbfertige. Bitte gebt frühzeitig Bescheid, dann priorisieren wir gemeinsam.

---

### 📦 Paket 2 – Referenzdatensatz (Gold Standard)

**Frist: Freitag, 21.08., 18:00 Uhr**

**Ergebnis:** Eine Tabelle mit rund 20 Webseiten, die **von Hand** nach unserem eigenen Regelwerk bewertet wurden.

**Spalten:**

| URL | Muster-ID | Bewertung durch Mensch | Beleg (Screenshot) | Anmerkung |
|---|---|---|---|---|

Bewertung jeweils: `eindeutig` / `verdächtig` / `unauffällig`

**Warum das wichtig ist:** Nur mit dieser Referenz können wir in der Präsentation eine belastbare Aussage zur Treffgenauigkeit machen. Ein Team mit einer nachvollziehbaren Messung wirkt deutlich überzeugender als eines mit einer bloßen Demonstration.

**Auswahlkriterien für die Seiten:**
- ohne Anmeldung erreichbar
- deutschsprachig
- **etwa die Hälfte unauffällige Seiten.** Das ist entscheidend: Wir müssen messen können, wie oft unser System fälschlich Alarm schlägt. Ein System, das überall Verstöße sieht, ist wertlos.

**Das Entwicklungsteam liefert bis Donnerstagmorgen eine vorgeprüfte Kandidatenliste**, damit ihr nur Seiten bewertet, die technisch auch erfassbar sind.

---

### 📦 Paket 3 – Rechtliche Absicherung und Präsentationsteil

**Frist: Samstag, 22.08.**

Drei Ergebnisse:

**a) Formulierungsrichtlinie und Haftungsabsicherung**

Die Kernfrage: Welche Aussagen darf unser System überhaupt treffen?

Eine unzutreffend behauptete Rechtsverletzung kann für das Unternehmen rufschädigend sein und wettbewerbsrechtliche Ansprüche gegen *uns* auslösen (Anknüpfungspunkte: § 4 Nr. 1, Nr. 2 UWG, ggf. §§ 823, 824 BGB). Deshalb brauchen wir:

- eine verbindliche Wortliste: Welche Begriffe verwenden wir in welcher Bewertungsstufe? (Vorschlag zur Diskussion: `eindeutig` → „Prüfhinweis mit hoher Auffälligkeit", `verdächtig` → „Verdachtsmoment"; das Wort „Verstoß" als Feststellung möglichst vermeiden)
- den Haftungshinweis im Wortlaut, der in jedem Bericht erscheint
- eine kurze Einschätzung zur Zulässigkeit des automatisierten Abrufs öffentlich zugänglicher Seiten (Beobachtung öffentlicher Inhalte, keine Umgehung von Zugangssperren, keine Überlastung)

**b) Begründung des dreistufigen Bewertungsmodells**

Zwei bis drei Sätze, die in der Präsentation vorgetragen werden können: Warum unterscheiden wir zwischen `eindeutig`, `verdächtig` und `unklar` – und warum ist gerade die Stufe „unklar" ein Qualitätsmerkmal und kein Eingeständnis von Schwäche? Dieser Punkt zeigt der Jury juristisches Verständnis.

**c) Drei Präsentationsfolien**

1. Zuordnung der Muster zu den Normen
2. Beweisführung: Warum unsere Berichte verwertbar sind
3. Grenzen des Systems und Ausblick

> ⚠️ **Paket 3 muss zwingend bis Samstag fertig sein.** Ab Dienstag steht das Entwicklungsteam nicht mehr zur Verfügung (siehe Abschnitt 7). Alles, was danach noch offen ist, lässt sich nicht mehr im Produkt umsetzen.

---

## 7. Zeitplan

Die Präsentation findet am **Donnerstag, 27.08.** statt. Das Entwicklungsteam ist ab **Dienstag, 25.08.** nicht mehr verfügbar.

Daraus folgt: **Der Code muss am Sonntagabend fertig sein. Der Montag ist kein Entwicklungstag, sondern ein Übergabetag.**

| Tag | Entwicklungsteam | Juristisches Team | Gemeinsam |
|---|---|---|---|
| **Mi 19.08.** | Erfassungsschicht (Screenshot, HTML) | Einarbeitung, Beginn Paket 1 | Kickoff-Workshop: DP-001 und DP-002 gemeinsam erarbeiten |
| **Do 20.08.** | Signalauswertung, Regel-Engine | **Paket 1 fertig, 18:00** | Abendbesprechung: Regelwerk erstmals im System testen |
| **Fr 21.08.** | Countdown-Prüfung, Preisvergleich, Berichtsstruktur | **Paket 2 fertig, 18:00** | Nachmittags: Abgleich System ↔ menschliche Bewertung, erste Messwerte |
| **Sa 22.08.** | Zeitachse/Diff, Beweisbericht, Oberfläche | **Paket 3 fertig** | 23:00: Funktionsumfang wird eingefroren – ab hier keine neuen Funktionen |
| **So 23.08.** | Fehlerbehebung, Bereitstellung, Aufzeichnung der Vorführung | Präsentation ausarbeiten | 3× vollständige Generalprobe |
| **Mo 24.08.** | **Übergabe**, Dokumentation, Fragenkatalog | Präsentation üben | Abschließende Probe; Team muss die Vorführung **ohne** das Entwicklungsteam durchführen können |
| Di 25.08. – Mi 26.08. | *nicht verfügbar* | Feinschliff der Präsentation | – |
| **Do 27.08.** | – | – | **Präsentation** |

### Was das für euch konkret bedeutet

Am Montagabend muss folgender Satz zutreffen:

> *Jedes Teammitglied kann die Vorführung eigenständig von Anfang bis Ende durchführen und die zehn wahrscheinlichsten Rückfragen beantworten.*

Wir werden am Montag genau das testen: Eine Person aus dem juristischen Team führt die Demonstration allein durch. Wo es hakt, wird nachdokumentiert.

Zusätzlich als Absicherung: eine **Videoaufzeichnung der Vorführung** und eine **online erreichbare Version**, damit die Präsentation nicht von einem einzelnen Rechner abhängt.

---

## 8. Was wir bewusst weglassen

Klarheit über den Ausschluss ist genauso wichtig wie Klarheit über den Umfang.

**Nicht im Umfang:**
- vollständige Automatisierung eines Bestellvorgangs bis zum Zahlungsabschluss
- Seiten hinter einer Anmeldung
- mobile Anwendungen
- alle gängigen Dark-Pattern-Kategorien (es gibt weit über zwanzig – wir bearbeiten sechs)
- eine aufwendig gestaltete Benutzeroberfläche
- Benutzerverwaltung, Rechtekonzept, Mandantenfähigkeit

Wer während der Bearbeitung eine gute zusätzliche Idee hat: bitte in die Ideensammlung eintragen. Wir sprechen sie in der Präsentation als Ausblick an – aber wir bauen sie nicht.

---

## 9. Zusammenarbeit im Alltag

**Zwei kurze Abstimmungen täglich, je 15 Minuten** (morgens und abends). Drei Fragen:
1. Was ist seit gestern **fertig geworden**? (nicht: „woran arbeite ich")
2. Was wird heute fertig?
3. Wo hängt es – insbesondere: warte ich auf das jeweils andere Teilteam?

**Entscheidungsprotokoll:** Jede Festlegung mit Datum und Begründung in einer gemeinsamen Datei. Beispiel: *„20.08. – Art. 25 DSA nicht als eigenständiges Bewertungsmuster, da Art. 25 Abs. 2 DSA eine Subsidiarität gegenüber UWG und DSGVO anordnet."* Das erspart uns doppelte Diskussionen und liefert Material für die Fragerunde.

**Eine Bitte an das juristische Team:** Wenn eine Frage aus dem Entwicklungsteam kommt, ist die hilfreichste Antwort selten ein Absatz Fließtext. Hilfreich ist eine Liste von Bedingungen, die mit Ja/Nein oder einer Zahl beantwortbar sind. Wenn eine Frage sich so nicht beantworten lässt, ist das ebenfalls ein wichtiges Ergebnis – dann gehört das Merkmal in die Stufe „unklar", und genau das ist eine bewusste, verteidigbare Entscheidung.

---

## 10. Unsere Argumentationslinie für die Präsentation

Ein Satz, an dem sich alles ausrichtet:

> **„Dark Patterns zu finden ist einfach. Schwierig ist es, sie so zu dokumentieren, dass man damit arbeiten kann."**

Drei Belege dafür:

1. **Beweisfähigkeit** – Jeder Befund enthält Screenshot, Prüfsumme des Seitenzustands, Zeitstempel und Normzuordnung. Das Ergebnis ist so aufbereitet, dass es einer Abmahnung beigefügt werden kann.

2. **Nachvollziehbarkeit** – Jede Bewertung lässt sich lückenlos zurückverfolgen: gemessenes Signal → Bedingung im Regelwerk → Norm. Kein Befund beruht auf einer nicht überprüfbaren Modellentscheidung. Das dreistufige Modell verhindert bewusst Übertreibung.

3. **Zeitachse** – Wir bauen keinen Scanner, sondern einen **Monitor**. Wir erkennen auch, wenn ein Unternehmen eine beanstandete Gestaltung später wieder einführt. Damit besteht ein unmittelbarer Anschluss an die Durchsetzung von Unterlassungserklärungen.

---

## 11. Checkliste für das Kickoff-Treffen heute

- [ ] Zeitplan und Nichtverfügbarkeit ab 25.08. allen bekannt
- [ ] Teilnahme an der Präsentation am 27.08. geklärt
- [ ] Produktdefinition in einem Satz gemeinsam formuliert
- [ ] DP-001 und DP-002 gemeinsam als Muster erarbeitet
- [ ] Signal-Liste bestätigt, Ergänzungswünsche notiert
- [ ] Paket 1 auf Personen verteilt
- [ ] Kandidatenseiten grob abgesteckt
- [ ] Entscheidung: Werden Unternehmen in der Präsentation namentlich genannt oder anonymisiert? *(Empfehlung: anonymisieren – „Shop A", „Anbieter B" – sofern nicht ohnehin öffentlich beanstandet)*
- [ ] Präsentierende festgelegt *(Empfehlung: eine Person aus jedem Teilteam)*
- [ ] Gemeinsame Ablage, Entscheidungsprotokoll und Ideensammlung eingerichtet
- [ ] Zeiten der täglichen Abstimmungen festgelegt

---

## Anhang: Begriffe für das Entwicklungsteam

| Begriff | Bedeutung |
|---|---|
| Verstoß | Rechtsverletzung |
| Prüfschema | Prüfreihenfolge / Checkliste – bei uns: das Regelwerk |
| Abmahnung | förmliche Aufforderung, ein Verhalten zu unterlassen |
| Unterlassungserklärung | verbindliche Zusage, das Verhalten künftig zu unterlassen; bei Zuwiderhandlung Vertragsstrafe |
| Anspruchsgrundlage | Norm, aus der sich ein Anspruch ergibt |
| Erwägungsgrund (ErwG) | Auslegungshilfe im Vorspann europäischer Rechtsakte |
| Rechtsprechung / Urteil / Aktenzeichen | Entscheidungspraxis der Gerichte |
| h. M. (herrschende Meinung) | überwiegend vertretene Auffassung |
| str. (streitig) | umstritten – bei uns Anlass für die Stufe „unklar" |
| Beweisfähigkeit | Eignung, im Verfahren als Beweismittel zu dienen |
