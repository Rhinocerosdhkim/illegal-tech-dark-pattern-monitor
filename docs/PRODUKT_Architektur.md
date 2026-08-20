# Produktarchitektur — vom Link zur Beweisakte

**Fassung 1.0 · Stand 20.08.2026** · ergänzt [`STRATEGIE.md`](STRATEGIE.md) §4 und §5
Adressat: **Entwicklung.** Abschnitt 4 betrifft auch das juristische Team — dort steht, was wir in der Präsentation über KI sagen und was nicht.

> [`STRATEGIE.md`](STRATEGIE.md) sagt, **was** wir bauen und **warum**.
> Dieses Dokument sagt, **wie das Produkt abläuft**: von der eingegebenen Adresse bis zur fertigen Beweisakte — wer welchen Schritt verantwortet, welche Datei dabei entsteht, und an welchen Stellen ein Sprachmodell arbeitet.

---

## 1. Das Produkt in einem Satz

> **Man gibt eine Webseite hinein. Die Maschine klickt sich selbst durch den Bestellweg, misst, prüft das Gemessene gegen ein von Jurist:innen geschriebenes Regelwerk und gibt eine Beweisakte aus — Screenshot, Hash, Zeitstempel, Norm. Über viele Seiten hinweg entsteht daraus eine filterbare Marktübersicht. Geprüft wird nach Regeln, entschieden wird von Menschen.**

### Nutzungsszenario

Eine Mitarbeiterin der Verbraucherzentrale will den Ticketzweitmarkt untersuchen. Bisher: Seite öffnen, klicken, Screenshot, in Word einfügen, Norm nachschlagen, für zwanzig Seiten wiederholen. Wir ersetzen nicht ihr Urteil. Wir machen ihre Dokumentation **verwertbar**, **wiederholbar** und **vergleichbar über die Zeit**.

---

## 2. Die Verarbeitungskette

```
   [1] AUFTRAG        eine URL  oder  ein Dokument mit einer Linktabelle
        │                                        ↑ KI ②  Dokument → Zielliste, branche
        ▼
   [2] ERFASSUNG      Playwright läuft den PFAD ab, nicht eine URL
        │             je Schritt: Screenshot · DOM-Hash · Zeitstempel
        │                                        ↑ KI ③  „welches Element führt weiter?"
        ▼
   capture.json       ← Vertrag zwischen Erfassung und Auswertung, eingefroren
        │
        ▼
   [3] SIGNALE        messbare Fakten: px², Kontrast, Klicktiefe, MwSt-Hinweis
        │             jeder Wert trägt Schritt + Nachweis-Screenshot mit sich
        │             nicht messbar → signal_errors, niemals null/0/false
        │                                        ↑ KI ①  nur Textdeutung, mit Konfidenz
        ▼
   [4] REGELWERK      ★ hier arbeitet das juristische Team ★     rules/*.yaml
        │             ►►► HIER KEINE KI ◄◄◄
        ▼
   [5] BEFUND         eindeutig · verdächtig · unklar · unauffällig
        │
        ├──────────────────────────────┬───────────────────────────┐
        ▼                              ▼                           ▼
   BEWEISAKTE                    MARKTÜBERSICHT              [6] ZEITACHSE
   eine Seite, PDF               viele Seiten, HTML          zwei Erfassungen
   Anlage zur Abmahnung          Filter + Statistik          im Vergleich
        ↑ KI ④ Berichtstext           ↑ KI ④ Zusammenfassung
```

---

## 3. Die Schritte im Einzelnen

### 3.1 Auftrag

Zwei Eingabewege, dasselbe Ergebnis:

| Weg | Eingabe | Ergebnis |
|---|---|---|
| Einzelprüfung | eine URL | ein Prüfauftrag |
| Sammelprüfung | CSV/XLSX/DOCX mit einer Linktabelle | eine Liste von Prüfaufträgen |

Beim zweiten Weg liest **KI ②** das Dokument, zieht die Adressen heraus und schlägt je Zeile eine `branche` vor (Ticketing, Reise, Mode, Telekommunikation …). Ein Mensch sieht die Liste durch und korrigiert.

> **Warum `branche` schon hier gebraucht wird:** Ohne sie gibt es später keine Statistik nach Branche — und genau die hat die Verbraucherzentrale im Seminar ausdrücklich verlangt. Was in Schritt 1 fehlt, fehlt in Schritt 5 endgültig.

### 3.2 Erfassung

Ein Ziel ist **eine Schrittfolge, keine URL** (Begründung: [`STRATEGIE.md`](STRATEGIE.md) §4.2):

```
Startseite → Suche/Kategorie → Produktdetail → Warenkorb → Bestellübersicht
```

Je Schritt entstehen: **Screenshot**, **DOM-Hash**, **Zeitstempel**. Fest verdrahtet und nie den Voreinstellungen überlassen: `viewport`, `locale: de-DE`, `timezone: Europe/Berlin`, `user_agent`. Ohne festes Viewport sind Pixelflächen bedeutungslos.

**Das ist der Kern des Produkts.** Die Verbraucherzentrale hat das Problem selbst benannt: *„so viele Nutzer haben sich das Produkt zuletzt angeschaut"* wird erst sichtbar, wenn man das Produkt anklickt. Ein Werkzeug, das eine URL aufruft und misst, findet diese Muster nie. Wir finden sie.

**Wenn ein Schritt scheitert:** Erfassung hält an, **alles bisher Gemessene bleibt erhalten**, die nicht erreichten Signale gehen mit Begründung nach `signal_errors`. Eine Teilerfassung ist weiterhin brauchbar — und erzeugt genau die Stufe `unklar`.

**Abrufe bleiben zurückhaltend:** nur öffentlich zugängliche Seiten, keine Umgehung von Zugangssperren, keine Anmeldung, spürbare Verzögerung zwischen Abrufen, nie zwei Ziele parallel. Ein Werkzeug, das Rechtsverstöße dokumentiert, darf sich seine Beweise nicht auf angreifbarem Weg beschaffen.

### 3.3 Signale

Aus dem Erfassten werden **Zahlen und Ja/Nein** gezogen. Keine Deutung, keine Bewertung.

```jsonc
"signals": {
  "accept_button_area_px2": { "wert": 4200,  "schritt": "startseite",    "nachweis": "S-01.png" },
  "reject_click_depth":     { "wert": 3,     "schritt": "startseite",    "nachweis": "S-01.png" },
  "scarcity_value":         { "wert": 3,     "schritt": "produktdetail", "nachweis": "S-02.png" },
  "vat_disclosure_present": { "wert": false, "schritt": "produktdetail", "nachweis": "S-02.png" }
}
```

**Jeder Messwert führt mit, wo er gemessen wurde und welcher Screenshot ihn belegt.** Das ist der gesamte Unterschied zwischen einem Bericht und einer Beweisakte. Ein nackter Wert lässt sich später nicht an ein Beweismittel binden, und damit fällt die juristische Argumentation in sich zusammen.

**KI ①** arbeitet hier — und nur an Text. Ob „Nur noch 2 verfügbar" eine Knappheitsbehauptung ist, ob eine Buttonbeschriftung der Formulierung `zahlungspflichtig bestellen` gleichkommt, ob eine Textstelle ein Umsatzsteuerhinweis ist. Reguläre Ausdrücke scheitern an der Formulierungsvielfalt des Deutschen. Ausgabe ist **Signalwert plus Konfidenz**; bei niedriger Konfidenz wandert das Signal nach `signal_errors` und die Regel wird `unklar`.

> ⚠️ **Die eine Regel, deren Verletzung unsere Ergebnisse still verdirbt:**
> Was nicht gemessen werden konnte, wird **niemals** als `null`, `0`, `false` oder `-1` geschrieben.
> `false` heißt „gemessen, und es ist nicht vorhanden". `signal_errors` heißt „wir konnten es nicht prüfen".
> Juristisch sind das zwei völlig verschiedene Aussagen.

### 3.4 Regelwerk — ★ keine KI ★

Die Messwerte laufen gegen `rules/DP-00X.yaml`, geschrieben vom juristischen Team:

```yaml
verdict_rules:
  eindeutig:
    - "reject_click_depth > 1"
    - "accept_button_area_px2 / reject_button_area_px2 > 2.0"
  verdaechtig:
    - "preselected_checkbox_count > 0"
```

Ergebnis ist eine von vier Stufen:

| Stufe | Bedeutung | Woher |
|---|---|---|
| `eindeutig` | schwer zu bestreiten | Regel trifft |
| `verdächtig` | Anhaltspunkt, Auslegungsspielraum | Regel trifft |
| `unklar` | **benötigtes Signal nicht erhoben** | **automatisch aus `signal_errors`** |
| `unauffällig` | nichts trifft zu | Rückfall |

**`unklar` müssen wir nicht bauen — die Stufe entsteht aus der Architektur von selbst.** Wer ein Signal nicht messen konnte, kann über die zugehörige Regel nichts behaupten. Das ist kein Eingeständnis von Schwäche, sondern der Mechanismus, der uns davon abhält, Ungemessenes zu behaupten (§ 4 Nr. 1, Nr. 2 UWG).

Jede Regel trägt zusätzlich `kategorie` — genau einer der vier Werte der Verbraucherzentrale: **Zeitdruck · Zwang · Hindernisse · Irreführung**. Danach wird in der Marktübersicht gefiltert.

### 3.5 Ausgabe — zwei Erzeugnisse aus denselben Daten

**A · Beweisakte** — eine Seite, PDF, Anlage zur Abmahnung

| Nr. | Befund | Gemessener Wert | Kategorie | Norm | Stufe | Nachweis |
|---|---|---|---|---|---|---|
| 1 | Countdown springt nach Löschen aller Browserdaten auf denselben Startwert | `countdown_resets_on_revisit = true`, 900 s | Zeitdruck | Anh. zu § 3 III UWG Nr. 7 | eindeutig | S-02, S-03 · 2 Messungen · `sha256:a1b2…` |
| 2 | Ablehnung erfordert mehr Schritte als Zustimmung | `reject_click_depth = 3` (Zustimmung 1) | Hindernisse | Art. 7 IV DSGVO | eindeutig | S-01 · 20.08.2026 14:22:03 |
| 3 | Kein Umsatzsteuerhinweis im Preisumfeld | `vat_disclosure_present = false` | Irreführung | § 6 PAngV → § 3a UWG | verdächtig | S-04 · Produktdetail |

Jede Zeile ist lückenlos rückverfolgbar: **Screenshot → Messwert → Bedingung im Regelwerk → Norm.** **KI ④** formuliert daraus den deutschen Fließtext — sie beschreibt, sie entscheidet nicht.

**B · Marktübersicht** — viele Seiten, HTML mit Filtern

Filter: Branche · Kategorie · Norm · Befundstufe · Zeitraum.
Statistik: Befunde je Branche, häufigste Kategorie, häufigste Norm, Veränderung gegenüber der letzten Erfassung. Export als PDF und CSV.

> Der Gold Standard aus Paket 2 (~20 Seiten) **ist** der Inhalt dieser Übersicht. Aus einer Messaufgabe wird zugleich der Demo-Inhalt.

### 3.6 Zeitachse

Dieselbe Prüfung drei Wochen später. Zwei Erfassungsdateien werden verglichen:

```
DP-003  Countdown      eindeutig    → unauffällig   (entfernt)
DP-001  Consent        unauffällig  → eindeutig     ← still wieder eingeführt
```

**Das ist der Unterschied zwischen einem Scanner und einem Monitor** — und der Anschluss an die Durchsetzung von Unterlassungserklärungen, wo eine Vertragsstrafe fällig wird.

---

## 4. Wo KI eingesetzt wird — und wo ausdrücklich nicht

> ### **„KI navigiert. Das Recht entscheidet."**

Unser stärkstes Argument ist, dass die **Befundentscheidung ohne Modell** zustande kommt ([`DECISIONS.md`](DECISIONS.md), 19.08.). Wer dieses Argument durch beliebig verteilte KI verwässert, verliert mehr, als er gewinnt. Deshalb: KI nur dort, wo sie einen **echten Engpass** beseitigt.

| | Stelle | Aufgabe | Warum unbedenklich | Aufwand |
|---|---|---|---|---|
| **①** | Textdeutung (3.3) | Formulierungsvarianten erkennen: Knappheit, Buttonbeschriftung, MwSt-Hinweis | Ausgabe ist Signal **plus Konfidenz**; niedrige Konfidenz → `unklar`. Vom Briefing bereits vorgesehen | gering |
| **②** | Dokumentimport (3.1) | Linktabelle → Zielliste, `branche` vorschlagen | berührt keine Bewertung, Mensch prüft nach | gering |
| **③** | Pfadnavigation (3.2) | aus dem A11y-Baum entscheiden, welches Element zur Produktdetailseite führt | **prüfbar** — jeder Schritt liegt als Screenshot vor. Trifft keine rechtliche Aussage | mittel |
| **④** | Berichtstext (3.5) | Beweisakte-Fließtext, Zusammenfassung der Marktübersicht | arbeitet nur auf bereits feststehenden Zahlen. Vom Briefing bereits vorgesehen | gering |
| **✗** | **Befundstufe (3.4)** | — | **ausgeschlossen.** Ein Befund aus einer Modellentscheidung ist weder reproduzierbar noch im Verfahren begründbar | — |

**③ löst zusätzlich ein Risiko aus [`STRATEGIE.md`](STRATEGIE.md) §8:** wechselnde Selektoren. Ein regelbasierter Ablauf verrottet und braucht dauerhaft Entwicklerpflege — eine navigierende KI findet das Element neu. Das ist die Fortsetzung unseres Kernarguments **bezahlbar**: Die Verbraucherzentrale soll das Werkzeug ohne Entwicklungsteam weiterbetreiben können.

**Für die Präsentation:**

> *„Andere setzen KI dorthin, wo sie schadet — in die Entscheidung. Wir setzen sie dorthin, wo sie hilft — ins Finden. Und wir schreiben auf eine Folie, wo wir sie nicht einsetzen."*

Eine juristische Jury honoriert die zweite Hälfte dieses Satzes stärker als die erste.

---

## 5. Die Oberfläche

`README.md` schließt eine **aufwendige** Oberfläche aus. Das gilt weiter. Was wir bauen, ist eine **dünne Hülle um die bestehende Kette** — kein zweites Produkt.

**Drei Ansichten:**

| | Ansicht | Inhalt |
|---|---|---|
| 1 | **Auftrag** | URL eingeben oder Dokument ablegen → Prüfliste |
| 2 | **Prüflauf** | der ablaufende Pfad, eintreffende Screenshots, sich füllende Signale |
| 3 | **Ergebnis** | Beweisakte · Marktübersicht · Zeitachse |

**Zwei Betriebsarten, und das ist keine Kosmetik:**

- **Referenzfälle** — bereits erfasste Läufe, werden nur angezeigt. Startet sofort, kann nicht scheitern.
- **Neue Prüfung** — echte Erfassung. Dauert, kann scheitern.

> **Architektonische Folge, heute zu berücksichtigen:** Erfassung (langsam, offline, erzeugt Dateien) und Anzeige (sofort, liest `out/`) werden **getrennt**. Die Vorführung läuft auf vorab erfassten Läufen; eine Live-Prüfung ist Zugabe, nicht Voraussetzung. viagogo hat Bot-Erkennung, und ein Pfadlauf dauert 60–90 Sekunden — darauf darf die Präsentation nicht angewiesen sein.

**Warum die Oberfläche keine Scope-Ausweitung ist:**

1. **Übergabe am Montag.** Ab Dienstag ist keine Entwicklung verfügbar; eine Person aus dem juristischen Team muss die Vorführung allein bedienen. Ein Kommandozeilenaufruf ist dabei das Risiko, ein Startknopf die Absicherung.
2. **Die Marktübersicht war ohnehin als HTML mit Filtern geplant** ([`STRATEGIE.md`](STRATEGIE.md) §2). Rund zwei Drittel der Arbeit stehen also bereits im Plan. Es kommen hinzu: Eingabeansicht, Laufansicht, Startknopf.
3. **Die Jury ist nicht technisch besetzt.** Ein PDF im Ausgabeordner überzeugt sie nicht; eine Maschine, der man beim Klicken zusieht, überzeugt sie.

Weiterhin **nicht** im Umfang: Nutzerkonten, Rechteverwaltung, Datenbank, gestalterischer Aufwand über das Lesbare hinaus.

---

## 6. „Ein Link genügt" gegen pfadbasierte Erfassung

Ein ungelöster Widerspruch, der benannt gehört: **Eine beliebige URL hat keinen hinterlegten Pfad.** Drei Ausbaustufen, aufeinander aufbauend:

| Stufe | Was funktioniert | Voraussetzung |
|---|---|---|
| **A · Oberflächensignale** | DP-001 Consent, DP-002 Button-Lösung, DP-004 Kündigungsbutton — auf der Startseite oder einen Klick entfernt | nichts, bereits geplant |
| **B · Zielbeschreibung von Hand** | alles, aber je Seite 20–30 Minuten Handarbeit (`data/targets/*.yaml`) | skaliert nicht |
| **C · KI-Navigation** | alles, auf beliebigen Seiten | KI ③ |

**Wichtig: Stufe A ist bereits ein tragfähiges Produkt.** Was nicht erreicht wurde, wird `unklar` — nicht falsch. **Das Dreistufenmodell deckt den Fehlerfall der Oberfläche bereits ab**, und zwar ehrlich. Wir beginnen mit A, halten B für die Referenzfälle vor und bauen C nur, wenn die Erfassung am Freitag stabil läuft.

---

## 7. Verzeichnisaufteilung

Getrennte Verzeichnisse je Person, damit wir uns nicht ins Gehege kommen (vgl. [`AGENDA_Technik.md`](AGENDA_Technik.md) §4):

```
src/
  capture/          Karthik — Playwright, Pfadabarbeitung, schreibt capture.json
  signals/
    extractors.js   Karthik — reines Browser-JS, ohne Playwright-Abhängigkeit
                              läuft unverändert als Content Script (Extension)
  engine/           Donghyun — YAML laden, Bedingungen auswerten, Befundstufe
  report/           Donghyun — Beweisakte (PDF), Marktübersicht (HTML), Zeitachsen-Diff
  ui/               Donghyun — die drei Ansichten aus Abschnitt 5
  ai/               ① Textdeutung  ② Dokumentimport  ③ Navigation  ④ Berichtstext
                    ausschließlich hier — kein Modellaufruf in engine/
data/
  targets/          Zielbeschreibungen: name, branche, start, pfad
out/
  <run_id>/         capture.json · S-*.png · beweisakte.pdf
```

> **`src/ai/` ist bewusst ein eigenes Verzeichnis.** Wenn jemand fragt, wo bei uns KI arbeitet, ist die Antwort ein Verzeichnis mit vier Dateien — und `src/engine/` ist nachweislich nicht darunter. Das ist zugleich Architektur und Argument.

---

## 8. Baureihenfolge

**Nichts aus diesem Dokument ist Arbeit für heute Abend.** Heute gilt weiterhin nur: das Walking Skeleton.

| Wann | Was |
|---|---|
| **Do 20.08. abends** | Skeleton: viagogo → Erfassung → **eine** Regel → **eine** Tabellenzeile → PDF. **Ohne KI, ohne Oberfläche.** |
| **Fr 21.08.** | Beweisakte fertig · **KI ①** (Textdeutung — billig, wirkt sofort auf MwSt und Knappheit) |
| **Sa 22.08.** | Marktübersicht · die drei Ansichten · **KI ②** und **④** · **23:00 Feature Freeze** |
| **KI ③** | nur beginnen, wenn die Erfassung Freitagabend stabil läuft. Sonst Stufe A + Zielbeschreibungen von Hand, und ③ wird in der Präsentation als nächster Schritt genannt |
| **So 23.08.** | Fehlerbehebung · Demo-Video · online erreichbare Fassung |
| **Mo 24.08.** | Übergabe. Eine Person aus dem Recht führt allein vor |

**Kein zweites Signal, bevor das erste die ganze Kette durchlaufen hat.**

---

## 9. Ablauf der Vorführung, 90 Sekunden

Die Marktübersicht belegt den **Umfang**. Überzeugt wird die Jury von der **Laufansicht**.

1. viagogo einfügen, starten
2. Man sieht die Maschine klicken: Startseite → Suche → Produktdetail.
   *„Genau das Problem, das Sie im Seminar genannt haben — dieses Muster steht nicht auf der Startseite."*
3. Countdown auf der Produktdetailseite · Browserzustand leeren · erneut aufrufen · **derselbe Startwert**
   → Anhang zu § 3 Abs. 3 UWG Nr. 7. Visuell schwer zu bestreiten.
4. Beweisakte als PDF ausgeben — **ausgedruckt an die Jury weiterreichen.**
   Ein Blatt in der Hand wirkt bei einer juristischen Jury stärker als zehn Folien.
5. Umschalten auf die Marktübersicht, nach Branche filtern, Statistik zeigen

---

## 10. Offene Entscheidungen

Nach der Abstimmung im Team gehören die Antworten nach [`DECISIONS.md`](DECISIONS.md) — **nicht in einen Chatverlauf.**

- [ ] Oberfläche wird gebaut: **ja/nein**, und bleibt sie auf drei Ansichten begrenzt?
- [ ] Trennung Erfassung/Anzeige — bestätigt? (Vorführung läuft auf vorab erfassten Läufen)
- [ ] KI ① und ② werden gebaut — bestätigt?
- [ ] KI ③ (Navigation): Entscheidung vertagt auf **Freitagabend**, abhängig von der Stabilität der Erfassung — einverstanden?
- [ ] Konfidenzschwelle für KI ①, unterhalb derer das Signal nach `signal_errors` geht
- [ ] Welches Modell, und läuft es ohne Schlüssel im Übergabefall? *(Montagsübergabe: keine Umgebungsvariablen, keine Einrichtung)*
- [ ] Formulierung für die Präsentation abgestimmt: „KI navigiert, das Recht entscheidet"
- [ ] Name des einen Startbefehls (offen seit [`AGENDA_Technik.md`](AGENDA_Technik.md) §8)
