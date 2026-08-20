# Abstimmungsbedarf Regelwerk — DP-004, DP-005, DP-006

**Stand 20.08.2026 · Branch `jura/paket-1-dp004-006`**
Grundlage: die juristische Ausarbeitung von Sebastian vom 20.08., 01:05–01:17 (ursprünglich PR #1–#3).

Die **rein mechanischen Fehler sind bereits behoben** (siehe Abschnitt 7). Was hier steht, kann das Entwicklungsteam **nicht allein entscheiden** — es braucht eine gemeinsame Festlegung, und zwar **heute vor 18:00**, weil danach Paket 1 abgeschlossen sein soll.

Vorweg, weil es untergehen könnte: Die juristische Arbeit ist gut. Der Tatbestand zu § 312k BGB folgt sauber der Absatzstruktur, die Anspruchskette über § 3a UWG stimmt, und die Fehlalarmlisten sind keine Pflichtübung, sondern enthalten echte Einwände. **DP-006 verzichtet bewusst auf die Stufe `eindeutig` und begründet das** — das ist genau die Zurückhaltung, die wir brauchen. Die Punkte unten betreffen die Schnittstelle, nicht die Rechtsanwendung.

---

## 1. Rund 40 Signale, die es nicht gibt — der Hauptpunkt

In den drei Regeln stehen etwa 40 Signalnamen, die nicht in [`_SIGNALE.md`](../rules/_SIGNALE.md) stehen. Die Regeln sind damit **derzeit nicht ausführbar**.

Das ist aber **nicht einfach ein Regelverstoß.** Ein Teil dieser Signale ist juristisch berechtigt: § 312k BGB setzt ein Dauerschuldverhältnis voraus, und unser vorhandenes `has_recurring_contract_keywords` sucht lediglich nach Wörtern wie „Abo". Der Einwand, dass das rechtlich nicht trägt, ist richtig. Wir müssen also nicht die Regeln zurechtstutzen, sondern die Signalliste nachverhandeln.

Vorschlag: drei Körbe.

### Korb A — messbar und billig → **kommt in `_SIGNALE.md`**

| Gewünschtes Signal | Anmerkung |
|---|---|
| `has_confirmation_page` | Bestätigungsseite vorhanden ja/nein |
| `confirmation_page_directly_reached` | ohne Zwischenschritt erreicht |
| `kuendigungsbutton_requires_login` | Anmeldung vorgeschaltet |
| `kuendigungsbutton_hidden_in_menu` | nur über aufklappbares Menü erreichbar |
| `has_price_display` | überhaupt ein Preis auf der Seite |
| `shipping_cost_amount` | Betrag in Euro |
| `gratis_claim_scope` | Wortlaut des Gratis-Versprechens |
| `required_info_type` | welches Stichwort gegriffen hat (Widerruf, Impressum …) |
| `preselected_paid_addon_amount` | Betrag der vorausgewählten Zusatzleistung |

### Korb B — schon vorhanden, nur anders benannt → **umbenennen, nicht neu bauen**

| Gewünscht | Vorhanden |
|---|---|
| `is_consumer_offer` | `is_b2c_offer` |
| `listed_total_price` | `price_listed` |
| `shipping_cost_disclosed` | `shipping_cost_disclosed_on_product_page` |
| `first_price_display_timestamp`, `additional_cost_first_display_timestamp`, `price_history_within_current_journey` | **entfällt** — seit der Pfaderfassung führt *jedes* Signal mit, auf welchem Schritt es gemessen wurde (`schritt`) und welcher Screenshot es belegt. Der Zeitpunkt der Erstanzeige ergibt sich daraus von selbst |

Der letzte Punkt ist die gute Nachricht: Drei der aufwendigsten Wünsche sind durch die gestrige Architekturänderung **bereits erfüllt**.

### Korb C — rechtliche Bewertung, maschinell **nicht** feststellbar

| Signal | Warum es kein Signal sein kann |
|---|---|
| `is_dauerschuldverhaeltnis` | Vertragstypbestimmung |
| `is_consumer_contract` | Vertragstypbestimmung |
| `contract_concludable_on_website` | Auslegung des Angebots |
| `is_electronic_business_transaction` | rechtliche Einordnung |
| `entrepreneur_owes_paid_performance` | rechtliche Einordnung |
| `stricter_form_required`, `is_financial_services` | Normanwendung |
| `costs_are_unavoidable_delivery_or_offer_costs` | Ausnahme des Anhangs Nr. 20 — Wertung |
| `required_total_price_can_be_calculated`, `shipping_cost_can_be_calculated_in_advance` | „vernünftigerweise im Voraus berechenbar" ist ein Rechtsbegriff |
| `kuendigungsbutton_label_is_not_clearly_equivalent` | „entsprechend eindeutige Formulierung" ist Auslegung |
| `button_is_clearly_legible` | „gut lesbar" ist Wertung — messbar wären nur Schriftgröße und Kontrast als Indizien |

**Zur Entscheidung — zwei Wege:**

**Weg 1 (einfach):** Diese Merkmale entfallen aus `applies_when` und `verdict_rules`. Fehlt ein solches Merkmal, kann die Regel höchstens `verdaechtig` werden.

**Weg 2 (besser, Vorschlag des Entwicklungsteams):** Wir führen ein neues Feld ein:

```yaml
  menschliche_pruefung:
    - "Liegt ein Dauerschuldverhältnis vor?"
    - "Ist der Vertrag auf der Website abschließbar?"
```

Die Beweisakte druckt diese Punkte als **Prüfliste für die Juristin** unter den Befund. Das Werkzeug sagt dann: „Technisch festgestellt: A, B, C. Rechtlich noch zu prüfen: X, Y." Das ist ehrlicher als jede Schätzung — und es ist genau das, was eine Beweisakte leisten soll. Aufwand: rund zwei Stunden.

> **Empfehlung: Weg 2.** In der Präsentation ist das ein starker Punkt: Wir behaupten nicht, Recht anzuwenden, sondern bereiten die Anwendung vor.

---

## 2. Zwei verschiedene Schreibweisen für `verdict_rules`

DP-004 und DP-006 verwenden die Form aus der Vorlage:

```yaml
  verdict_rules:
    eindeutig:
      - "has_kuendigungsbutton == false"
```

DP-005 verwendet eine andere:

```yaml
  verdict_rules:
    eindeutig:
      - condition: "..."
        result: "LEGAL_RELEVANT"
        severity: "HIGH"
        reason: >
          ...
```

**Beides zugleich kann die Engine nicht — es muss eine Form werden.**

- Für die Objektform spricht das Feld `reason`: eine Begründung je Bedingung ist für die Beweisakte tatsächlich wertvoll.
- Gegen sie spricht `severity: HIGH/MEDIUM/LOW`. Das ist eine **zweite Schwereskala neben `eindeutig`/`verdächtig`/`unklar`**. Zwei Skalen nebeneinander sind eine Fehlerquelle, und `severity` müsste erklärt und verteidigt werden.

> **Empfehlung: Objektform mit `condition` und `reason`, aber ohne `severity`.** Dann bekommt jede Bedingung ihre Begründung, und es bleibt bei einer Skala. DP-004 und DP-006 müssten entsprechend angepasst werden — das ist reine Formsache, rund 20 Minuten.

---

## 3. `applies_when` — neue Struktur `all:` / `none:`

Sebastian hat eingeführt:

```yaml
  applies_when:
    all:  [ ... ]     # alle müssen zutreffen
    none: [ ... ]     # keines darf zutreffen
```

Die Vorlage kannte nur eine flache Liste ohne Verneinung.

> **Empfehlung: übernehmen.** Die Verneinung wird gebraucht (Beispiel: § 312k gilt nicht bei Finanzdienstleistungen), und mit einer flachen Liste ließe sich das nicht ausdrücken. DP-006 nutzt noch die flache Form und müsste angeglichen werden. Aufwand in der Engine: gering.

---

## 4. Der Produktname „PatternWatch"

Taucht dreimal in `explanation_template_de` auf und steht damit **wörtlich in jeder Beweisakte**. Der Name ist im Team nicht abgestimmt worden.

Zu klären: Ist das ein Vorschlag, oder wurde er irgendwo beschlossen? Bis zur Klärung wäre „Das System" die neutrale Formulierung, die auch das Briefing verwendet.

---

## 5. Zwei Schreibweisen für Platzhalter

Die Vorlage sieht `{signal_name}` vor — die Werte werden automatisch eingesetzt:

```yaml
    Der Ablehnen-Button misst {reject_button_area_px2} px².
```

In den neuen Regeln steht stattdessen `[BEFUND]`, `[INITIAL_PRICE]`, `[PRICE_DELTA]`.

Das ist keine Kleinigkeit: `{}` wird vom System ersetzt, `[]` bliebe als Text in der Beweisakte stehen. **Bitte auf `{signalname}` umstellen** — dabei muss der genaue Signalname verwendet werden, nicht ein freier Begriff.

---

## 6. Umfang: DP-005 ist doppelt so groß wie geplant

Die Ausarbeitung zu DP-005 deckt den vollständigen Bestellvorgang bis zur Kasse ab. Nach [`STRATEGIE.md` §4.3](STRATEGIE.md) hatten wir DP-005 geteilt:

- **DP-005a** — Preisangabe auf der Produktseite (Umsatzsteuer, Versandkosten genannt?): im Umfang, weil die Verbraucherzentrale die fehlende Mehrwertsteuer-Angabe ausdrücklich genannt hat
- **DP-005b** — Preisdifferenz bis zum Bestellabschluss: **nur bei Restzeit**, weil die Navigation bis zur Kasse nicht zuverlässig gelingt

Die vorliegende Fassung ist im Kern DP-005b. Die juristische Arbeit ist damit **nicht verloren** — sie ist die Vorlage für DP-005b, sobald wir dazu kommen.

> **Vorschlag:** Datei in zwei Regeln aufteilen. DP-005a bekommt die Bedingungen, die schon auf der Produktseite messbar sind; DP-005b behält den Rest und bleibt auf `status: ENTWURF`, bis klar ist, ob wir es schaffen.

---

## 7. Bereits behoben — keine Rückfrage nötig

| | Was | Wo |
|---|---|---|
| ✅ | `status: version 1.0` → `REVIEW` (kein zulässiger Wert) | alle drei |
| ✅ | `AND` → `and` (die Vorlage und der Parser erwarten Kleinschreibung) | DP-004, DP-005 |
| ✅ | In Bedingungen benutzte, aber nicht deklarierte Signale nachgetragen | DP-004, DP-005 |
| ✅ | `financial_services` → `is_financial_services` (zwei Schreibweisen für dasselbe) | DP-004 |
| ✅ | `offene_fragen: []` gefüllt — die Liste ist unsere Grundlage für die Fragerunde | DP-004 |
| ⚠️ | **`kuendigungsbutton_click_depth > 0` deaktiviert** | DP-004 |

Zum letzten Punkt: Eine Kündigungsschaltfläche liegt nie auf der Startseite selbst, die Klicktiefe ist also praktisch immer größer als 0. Die Bedingung hätte **auf jeder untersuchten Website ausgelöst** — und sie widerspricht dem eigenen `threshold_source`, der ausdrücklich festhält, dass die Klicktiefe nicht allein über die Rechtswidrigkeit entscheiden darf. Sie ist auskommentiert, nicht gelöscht; es fehlt nur ein belastbarer Wert oder die Entscheidung, sie zu streichen.

---

## 8. Und noch offen: DP-003

**DP-003 (Zeitdruck) hat noch niemand bearbeitet.** Nach [`STRATEGIE.md`](STRATEGIE.md) ist das unser Kernmuster — der Countdown-Nachweis über den Anhang zu § 3 Abs. 3 UWG Nr. 7 ist die einzige Regel, bei der wir `eindeutig` guten Gewissens vergeben, und er trägt das stärkste Argument der Präsentation.

Bitte heute zuweisen.
