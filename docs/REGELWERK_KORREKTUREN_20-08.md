# Korrekturen am Regelwerk — 20.08.2026

**An das juristische Team. Bitte gegenlesen.**
Alle Änderungen stehen als Kommentar in der jeweiligen Regeldatei, mit Begründung an Ort und Stelle. Wer eine für falsch hält: bitte zurückdrehen, das ist kein Widerspruch, sondern der Zweck dieser Liste.

Anlass: Die Engine läuft jetzt gegen drei Erfassungsläufe, darunter **eine bewusst unauffällige Seite**. Dabei ist sichtbar geworden, welche Bedingungen auf einer rechtmäßigen Website ausgelöst hätten. Ein Werkzeug, das überall Verstöße sieht, ist für eine Verbraucherzentrale wertlos — und macht uns nach § 4 Nr. 1, Nr. 2 UWG selbst angreifbar.

Jede Korrektur ist durch einen Test in [`tests/test_rule_defects.py`](../tests/test_rule_defects.py) abgesichert.

---

## 1. DP-002 — die Graue Liste war unerreichbar

**Befund.** `eindeutig` löste aus, wenn die Beschriftung *nicht auf der Weißliste* steht. `verdaechtig` löste aus, wenn sie *auf der Grauliste* steht. Keine der vier Formulierungen der Grauliste steht auf der Weißliste, und `eindeutig` wird zuerst geprüft — die Stufe `verdaechtig` konnte damit nie erreicht werden.

**Folge in der Sache.** Ein Shop mit „Jetzt bestellen" — einer Formulierung, deren Eindeutigkeit im Sinne des § 312j Abs. 3 BGB gerade **umstritten** ist — wurde als eindeutiger Verstoß ausgewiesen.

**Korrektur.** `eindeutig` verlangt jetzt zusätzlich, dass die Beschriftung auch nicht auf der Grauliste steht. Beide Listen sind in das Feld `listen:` umgezogen und lassen sich dort pflegen, ohne eine Bedingung anzufassen.

**Ergebnis am Referenzfall:** viagogo fällt bei DP-002 von `eindeutig` auf `verdaechtig`. Das ist die richtige Aussage.

## 2. DP-002 — Wortlaut statt Typografie

**Befund.** Verglichen wurde auf vollständige Zeichengleichheit. „Jetzt kaufen**!**" galt als Verstoß, „jetzt kaufen" nicht.

**Korrektur.** Beim Listenvergleich werden Satzzeichen und Zierzeichen am Rand abgeschnitten (in der Engine, nicht in der Regel). § 312j Abs. 3 BGB und EuGH C-249/21 stellen auf den **Wortlaut** der Schaltfläche ab, nicht auf ihre Interpunktion.

## 3. DP-001 — ein einzelnes Drittanbieter-Cookie

**Befund.** `third_party_cookies_before_consent > 0` → `eindeutig`. Ein eingebundenes CDN oder eine externe Schriftart genügte. Die Regel widersprach sich dabei selbst: ihre eigenen Fehlalarmrisiken halten fest, *„bei genau einem Cookie sollte manuell geprüft werden"*.

**Korrektur.** `> 1` → `eindeutig`, `== 1` → `verdaechtig`. § 25 Abs. 2 TDDDG nimmt technisch notwendige Speicherung ohnehin aus.

## 4. DP-001 — „Mehr Informationen" sauber abgebildet

**Befund.** Zwei Bedingungen, von denen die zweite von der ersten vollständig verschluckt wurde (`reject_button_present == false` deckt jeden Fall ab, in dem die längere Bedingung zuträfe).

**Korrektur.** Nach `legal_note_on_more_info`:
- **kein Ablehnen-Button und der „Mehr Informationen"-Weg führt nicht zur Ablehnung** → `eindeutig` (gar keine Wahl)
- **kein Ablehnen-Button, aber der Weg führt dorthin** → `verdaechtig` (Ablehnung spürbar erschwert, Art. 7 Abs. 4 DSGVO)

## 5. DP-003 — jeder Countdown war ein Verdachtsmoment

**Befund.** `countdown_element_present == true and countdown_resets_on_revisit != true` → `verdaechtig`. Das löst bei **jedem** Countdown aus, auch bei Sitzungsfristen und Zahlungs-Timeouts, die die eigenen Fehlalarmrisiken dieser Regel ausdrücklich ausnehmen wollen. Es widerspricht zudem dem eigenen `threshold_source`, der einen *reproduzierbaren Befund* verlangt, dass die behauptete Begrenzung nicht besteht — die Bedingung markierte gerade den Fall, in dem dieser Befund **nicht** erbracht wurde.

**Korrektur.** Gestrichen. Der Sachverhalt ist vollständig abgedeckt: springt der Countdown zurück → `eindeutig`; springt er nicht zurück → er ist echt; lässt es sich nicht messen → `unklar` entsteht von selbst.

## 6. DP-003 — Messlücke wurde als Befund gewertet

**Befund.** `scarcity_text_present == true and scarcity_value == 0` → `verdaechtig`. Ein Knappheitshinweis ohne lesbare Zahl („nur noch wenige verfügbar") liefert 0.

**Korrektur.** Gestrichen. In [`_SIGNALE.md`](../rules/_SIGNALE.md) steht jetzt: Ist keine Zahl lesbar, gehört `scarcity_value` nach `signal_errors` — nicht als 0 gemeldet.

## 7. DP-004 — die Regel war auf jeder Seite `unklar`

**Befund.** `applies_when` verlangte fünf rechtliche Qualifikationen, die niemand misst (`is_consumer_contract`, `contract_concludable_on_website`, `is_electronic_business_transaction`, `is_dauerschuldverhaeltnis`, `entrepreneur_owes_paid_performance`). Die Anwendbarkeit ließ sich nie prüfen, also stand die Regel auf **jeder** Seite auf `unklar` — obwohl ihre stärkste Bedingung, `has_kuendigungsbutton == false`, auf einem längst zugesagten Signal beruht.

**Korrektur**, nach ABSTIMMUNG Korb B/C:

```yaml
applies_when:
  all:  [ is_b2c_offer, order_button_found, has_price_display ]
  any:  [ recurring_price_notation_present, min_contract_term_stated,
          auto_renewal_text_present ]          # mindestens ein starkes Signal
  none: [ is_financial_services ]
applicability_derived: true
```

`stricter_form_required` ist nach `menschliche_pruefung` verschoben — es erfordert Kenntnis des Vertragstyps und ist kein Signal.

**Neu: `applicability_derived`.** Aus drei Tatsachensignalen auf ein Dauerschuldverhältnis zu schließen ist eine **Ableitung**, keine Feststellung — und sie ist je Produkt verschieden, lässt sich also nicht site-weit im Zielprofil bestätigen. Genau diesen Fall benennt C4. Setzt eine Regel das Feld, bleibt sie auf `verdaechtig` begrenzt. **Das ist ein neues Feld im Regelwerk — bitte bestätigen oder verwerfen.**

**Ergebnis:** Ein Abo-Shop ohne Kündigungsschaltfläche liefert jetzt `verdaechtig` statt `unklar`. Ein redaktionelles Portal ohne Bestellvorgang fällt sauber als `nicht anwendbar` heraus.

## 7a. DP-001 — die Voraussetzung war invertiert (dieselbe Fehlerart)

**Befund.** `applies_when: banner_detected == true`. Damit fiel **der schwerste Fall aus dem Bericht**: eine Seite, die **gar kein** Einwilligungsbanner zeigt und trotzdem Drittanbieter-Cookies setzt. Sie galt als `nicht anwendbar` und verschwand — obwohl dort schon keine Einwilligung im Sinne des § 25 Abs. 1 TDDDG vorliegt. Gefunden beim Nachgehen der Frage, was `banner_detected == false` bedeuten soll.

**Korrektur.**

```yaml
applies_when:
  any:
    - "banner_detected == true"
    - "third_party_cookies_before_consent > 0"
```

Neue `eindeutig`-Bedingung: `banner_detected == false and third_party_cookies_before_consent > 0`. Die Bedingungen zur Gestaltung der Schaltflächen sind jetzt ausdrücklich an `banner_detected == true` gebunden, damit sie auf einer bannerlosen Seite nicht ins Leere greifen. Ohne Banner **und** ohne Drittanbieter-Cookies greift die Regel weiterhin nicht — dann ist nichts zu beanstanden.

## 8. DP-006 — die Voraussetzung war invertiert

**Befund.** `applies_when: required_info_found == true`. Damit fiel **der schlimmste Fall, den diese Regel überhaupt erfassen soll, stillschweigend heraus**: Eine Seite ohne Widerrufsbelehrung — oder mit einer so gründlich verborgenen, dass die Stichwortsuche sie nicht findet — galt als `nicht anwendbar` und verschwand aus dem Bericht.

**Korrektur.** Das Merkmal ist aus `applies_when` heraus und steht jetzt als Befundbedingung: `required_info_found == false` → `verdaechtig` (nicht `eindeutig` — es kann auch eine Grenze unserer Stichwortsuche sein).

## 9. DP-006 — löste auf nahezu jeder Website aus

**Befund.** Drei Bedingungen lösten **einzeln** aus: `font_size_min_px < 12`, `text_contrast_min < 4.5`, `scroll_depth_of_required_info_pct > 75`. Jede Website hat ein Impressum in kleiner Schrift in der Fußzeile. Jede der drei widersprach dabei ihrer eigenen Begründung — `threshold_source`: *„Die Unterschreitung dieses Wertes begründet für sich allein keinen Verstoß"*; `false_positive_risks`: *„Eine Platzierung in der Fußzeile ist nicht automatisch unzulässig"*.

**Korrektur.** Getrennt in zwei Gruppen:
- **strukturelle Verbergung** trägt weiterhin für sich (`hidden_by_opacity_count > 0`, eingeklapptes Element, `aria-hidden`) — das ist ein aktives Verheimlichen nach § 5a Abs. 2 UWG
- **weiche Indizien** (Schriftgröße, Kontrast, Position) lösen nur noch **paarweise** aus

## 10. DP-005 — eine lauffähige Bedingung ergänzt

**Befund.** Alle acht Bedingungen beruhen auf Signalen aus DP-005b (Navigation bis zur Kasse), die es noch nicht gibt. Die Regel konnte nichts liefern.

**Korrektur.** `is_consumer_offer` → `is_b2c_offer` (Korb B), und die in `_SIGNALE.md` bereits vorgeschlagene Bedingung ergänzt:

```yaml
- condition: "gratis_claim_present == true and shipping_cost_amount > 0"
```

Beide Signale sind ✅. Damit deckt DP-005 den Anhang Nr. 20 zu § 3 Abs. 3 UWG ab, ohne auf DP-005b zu warten.

---

## Was jetzt noch offen ist

| | |
|---|---|
| **DP-001 bleibt auf realen Seiten `unklar`** | Die Bedingungen zu *nagging* (`banner_reappears_*`) und zum „Mehr Informationen"-Weg brauchen Signale, die als 🟡 neu in `_SIGNALE.md` stehen. Bis sie erhoben werden, ist DP-001 auf einer sauberen Seite `unklar` — inhaltlich richtig, aber es kostet uns die Aussage „unauffällig" |
| **`applicability_derived` bestätigen** | Neues Feld, siehe 7 |
| **`banner_detected == false`** | Erledigt durch 7a. `_SIGNALE.md` sagt bisher „Regel wird auf `unklar` gesetzt"; richtig ist `nicht anwendbar` — aber **nur**, wenn zugleich keine Drittanbieter-Cookies gesetzt werden. Genau so steht es jetzt in der Regel. Bitte den Satz in `_SIGNALE.md` entsprechend berichtigen |
| **DP-005b** | Bleibt zurückgestellt |
