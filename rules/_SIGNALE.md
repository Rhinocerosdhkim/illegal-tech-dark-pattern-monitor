# Verfügbare Signale

**Nur was hier steht, kann das System messen.** Im Feld `signals` einer Regel dürfen ausschließlich Einträge aus dieser Liste verwendet werden.

Stand: 19.08.2026 · Änderungen bitte über das Entwicklungsteam

---

## Statuslegende

| Status | Bedeutung |
|---|---|
| ✅ | wird bis Donnerstag implementiert – **darauf könnt ihr euch verlassen** |
| 🟡 | für Freitag/Samstag geplant – nutzbar, aber baut keine ganze Regel nur darauf |
| ⚪ | Idee, noch nicht zugesagt – **nur nach Rücksprache verwenden** |

---

## Consent-Banner und Bedienelemente

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `banner_detected` | bool | ✅ | Wurde überhaupt ein Consent-Banner gefunden? Ist dies `false`, wird die Regel automatisch auf `unklar` gesetzt |
| `accept_button_area_px2` | Zahl | ✅ | Fläche des Zustimmen-Buttons in Pixeln (Breite × Höhe) |
| `reject_button_area_px2` | Zahl | ✅ | Fläche des Ablehnen-Buttons in Pixeln |
| `accept_contrast_ratio` | Zahl | ✅ | Kontrast Text/Hintergrund nach WCAG, Bereich 1–21. Höher = auffälliger |
| `reject_contrast_ratio` | Zahl | ✅ | dasselbe für den Ablehnen-Button |
| `reject_click_depth` | Zahl | ✅ | Wie viele Interaktionsschritte bis zur vollständigen Ablehnung? Zustimmung in einem Klick = 1 |
| `reject_button_present` | bool | ✅ | Existiert auf der ersten Ebene überhaupt eine Ablehnen-Möglichkeit? |
| `preselected_checkbox_count` | Zahl | ✅ | Anzahl vorausgewählter Auswahlfelder im Banner |
| `third_party_cookies_before_consent` | Zahl | ✅ | Anzahl Drittanbieter-Cookies, die **vor** jeder Einwilligung gesetzt wurden |
| `banner_reappears_on_reject` | bool | 🟡 | Erscheint das Banner nach Ablehnung erneut? (sog. *nagging*) |
| `banner_reappears_count_24h` | Zahl | 🟡 | Wie oft erscheint das Banner innerhalb von 24 Stunden erneut? **Setzt mehrere Erfassungen voraus** — kommt mit der Zeitachse |
| `more_info_present` | bool | 🟡 | Bietet das Banner statt einer Ablehnung nur „Mehr Informationen" / „Einstellungen"? |
| `more_info_leads_to_reject` | bool | 🟡 | Führt dieser Weg zu einer unmittelbaren Ablehnmöglichkeit? |
| `more_info_click_depth` | Zahl | 🟡 | Wie viele Klicks von dort bis zur vollständigen Ablehnung? |

> **Hinweis zu `third_party_cookies_before_consent`:** Dieses Signal ist unabhängig von der Gestaltung des Banners. Es misst, ob bereits vor jeder Interaktion Tracking stattfindet. Technisch sehr zuverlässig.

---

## Buttons und Pflichtbeschriftungen

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `order_button_label` | Text | ✅ | Beschriftung des Bestellabschluss-Buttons im Wortlaut |
| `order_button_found` | bool | ✅ | Wurde ein solcher Button überhaupt gefunden? |
| `has_kuendigungsbutton` | bool | ✅ | Existiert ein Kündigungsbutton auf der Seite? |
| `kuendigungsbutton_label` | Text | ✅ | dessen Beschriftung im Wortlaut |
| `kuendigungsbutton_click_depth` | Zahl | 🟡 | Klicks von der Startseite bis zum Kündigungsbutton |

---

## Dringlichkeit und Knappheit

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `countdown_element_present` | bool | ✅ | Ist ein Countdown auf der Seite? |
| `countdown_initial_value_sec` | Zahl | ✅ | Startwert in Sekunden beim ersten Aufruf |
| `countdown_unchanged_scans` | Zahl | 🟡 | **Über wie viele aufeinanderfolgende Erfassungen ist der ANGEZEIGTE Wert unverändert?** Ein Zähler, der nicht läuft, zählt nichts herunter — stärkerer Nachweis als der Reset. Angefordert von PV, 20.08. |
| `countdown_personalized` | bool | 🟡 | Wird die Frist als individuell begrenzt dargestellt (Muster: 24 Std. ab Registrierung)? Bei personalisierten Fristen genügt eine einzige unveränderte Messung, bei allgemeinen sind drei nötig (PV, 21.08.) |
| `countdown_resets_on_revisit` | bool | ✅ | **Springt der Countdown nach Löschen aller Browserdaten und erneutem Aufruf auf denselben Startwert zurück?** |
| `countdown_text` | Text | ✅ | umgebender Text im Wortlaut |
| `scarcity_text_present` | bool | ✅ | Knappheitshinweis vorhanden (z. B. „nur noch 2 verfügbar") |
| `scarcity_value` | Zahl | ✅ | die genannte Stückzahl. **Ist keine Zahl lesbar** („nur noch wenige verfügbar"), gehört das Signal nach `signal_errors` — nicht als 0 melden. 0 hieße „gemessen und null Stück", und darauf würde eine Regel anschlagen |
| `scarcity_value_unchanged_scans` | Zahl | 🟡 | Über wie viele aufeinanderfolgende Scans ist der Wert unverändert? |
| `viewer_count_present` | bool | 🟡 | „17 Personen sehen sich das gerade an" |

---

## Preise

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `price_listed` | Zahl | ✅ | Preis auf der Produktseite in Euro |
| `price_at_checkout` | Zahl | 🟡 | Endpreis unmittelbar vor Bestellabschluss |
| `price_delta` | Zahl | 🟡 | Differenz in Euro |
| `price_delta_ratio` | Zahl | 🟡 | Verhältnis Endpreis / Listenpreis |
| `shipping_cost_disclosed_on_product_page` | bool | 🟡 | Werden Versandkosten schon auf der Produktseite genannt? |
| `preselected_paid_addon_count` | Zahl | 🟡 | Anzahl vorausgewählter kostenpflichtiger Zusatzoptionen |
| `gratis_claim_present` | bool | ✅ | Werbung mit „gratis / kostenlos / umsonst" auf der Seite |
| `vat_disclosure_present` | bool | ⚪ | Steht im Preisumfeld ein Hinweis auf die Umsatzsteuer („inkl. MwSt.", „inkl. Mehrwertsteuer")? |
| `vat_disclosure_scroll_pct` | Zahl | ⚪ | Position dieses Hinweises in Prozent der Seitenhöhe — misst „versteckt in der Kopf-/Fußzeile" |
| `price_step` | Text | ⚪ | Auf welchem Schritt des Pfades der Preis gemessen wurde (`produktdetail`, `warenkorb` …) |

> ⚠️ Die Signale mit 🟡 setzen voraus, dass wir bis zum Bestellabschluss navigieren können. Das gelingt nicht auf allen Seiten. Rechnet damit, dass DP-005 in der Vorführung teilweise mit manuell erfassten Werten arbeitet.

---

## Verdeckung von Informationen

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `required_info_found` | bool | ✅ | Wurde der gesuchte Pflichthinweis (z. B. Widerrufsbelehrung) überhaupt gefunden? |
| `font_size_min_px` | Zahl | ✅ | kleinste Schriftgröße im Pflichtinformationsbereich |
| `text_contrast_min` | Zahl | ✅ | geringster Kontrastwert dort |
| `hidden_by_opacity_count` | Zahl | ✅ | Anzahl Textelemente mit Deckkraft unter 0,5 |
| `scroll_depth_of_required_info_pct` | Zahl | ✅ | Position des Pflichthinweises in Prozent der Seitenhöhe (0 = ganz oben, 100 = ganz unten) |
| `required_info_in_collapsed_element` | bool | 🟡 | Steht der Hinweis in einem eingeklappten Bereich? |
| `aria_hidden_on_required_info` | bool | 🟡 | Ist der Hinweis für Screenreader ausgeblendet? |

> **Wichtige Einschränkung:** Das System erkennt Pflichtinformationen nur über Stichworte (`Widerruf`, `Impressum`, `Gesamtpreis`, `Lieferkosten` …). Ob ein Text im Rechtssinne eine wesentliche Information darstellt, kann es nicht beurteilen. Regeln auf dieser Grundlage sollten daher nicht die Stufe `eindeutig` verwenden.

---

## Vertragsart — ersetzt `is_dauerschuldverhaeltnis`

**Neu, 20.08.** Ob ein Dauerschuldverhältnis vorliegt, ist eine **rechtliche Qualifikation** — die kann das System nicht vornehmen. Die Tatsachen, auf die sie sich stützt, sind dagegen messbar. Die Regel nimmt die Qualifikation vor, nicht das System.

| Signal | Typ | Status | Bedeutung | Aussagekraft |
|---|---|---|---|---|
| `recurring_price_notation_present` | bool | ✅ | Preis mit Periodenangabe: „9,99 €/Monat", „pro Monat", „/Jahr" | **stark** |
| `recurring_price_period` | Text | ✅ | die erkannte Periode im Wortlaut (`Monat`, `Jahr`, `Woche`) | — |
| `min_contract_term_stated` | bool | ✅ | „Mindestlaufzeit", „Vertragslaufzeit 24 Monate" | **stark** |
| `auto_renewal_text_present` | bool | ✅ | „verlängert sich automatisch" | **stark** |
| `cancellation_terms_present` | bool | ✅ | „Kündigungsfrist", „monatlich kündbar" | mittel |
| `has_recurring_contract_keywords` | bool | ✅ | `Abo`, `Mitgliedschaft`, `Tarif` — **bereits vorhanden** | **schwach** |

> **Auswertung in der Regel:** mindestens ein **starkes** Signal → Regel greift, aber höchstens `verdaechtig`. Nur schwache Signale → `unklar`. Keines → Regel greift nicht.
>
> Das schwache Signal trägt allein nicht: Ein „Newsletter-Abo" ist unentgeltlich und begründet kein Dauerschuldverhältnis.
>
> **Gemessen wird auf der Produktdetailseite**, nicht auf der Startseite — ein Händler kann Einmalkäufe und Abonnements nebeneinander anbieten.

---

## Anwendbarkeit — weitere Kontextsignale

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `is_financial_services` | bool | ✅ | BaFin-Hinweis im Impressum, Stichworte `Versicherung`, `Kredit`, `Depot`, `Bausparen` |
| `order_button_found` | bool | ✅ | zahlungspflichtige Bestellschaltfläche vorhanden — **bereits vorhanden**, deckt zugleich `contract_concludable_on_website` und `is_electronic_business_transaction` ab |
| `has_price_display` | bool | ✅ | überhaupt eine Preisangabe auf der Seite |

---

## Kündigungsschaltfläche — Ergänzungen

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `kuendigungsbutton_hidden_in_menu` | bool | ✅ | steht nur in einem zugeklappten Bereich oder Aufklappmenü (`<details>`, `aria-expanded="false"`) |
| `kuendigungsbutton_font_size_px` | Zahl | ✅ | Schriftgröße der Beschriftung — messbares Indiz für „gut lesbar" |
| `kuendigungsbutton_contrast_ratio` | Zahl | ✅ | Kontrast der Beschriftung, dito |
| `kuendigungsbutton_requires_login` | bool | 🟡 | führt erst nach einer Anmeldeaufforderung weiter |

### Bestätigungsseite — zweites Element des § 312k Abs. 2

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `has_confirmation_page` | bool | 🟡 | eine Bestätigungsseite existiert |
| `confirmation_page_directly_reached` | bool | 🟡 | ohne Zwischenschritt erreicht |
| `confirmation_page_requires_login` | bool | 🟡 | zwischen Kündigungsschaltfläche und Bestätigungsseite steht eine Anmeldeaufforderung — rechtlich etwas anderes als `kuendigungsbutton_requires_login` |

### Bestätigungsschaltfläche — drittes Element des § 312k Abs. 2

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `has_confirmation_button` | bool | 🟡 | auf der Bestätigungsseite existiert eine Bestätigungsschaltfläche |
| `confirmation_button_label` | Text | 🟡 | deren Beschriftung im Wortlaut (*ersetzt* `kuendigungsbutton_confirm_label`) |
| `confirmation_button_font_size_px` | Zahl | 🟡 | Schriftgröße — Indiz für „gut lesbar", das das Gesetz für **beide** Schaltflächen verlangt |
| `confirmation_button_contrast_ratio` | Zahl | 🟡 | Kontrast, dito |

> **Warum diese Trennung:** § 312k Abs. 2 kennt **drei** Elemente — Kündigungsschaltfläche, Bestätigungsseite, Bestätigungsschaltfläche. Jedes hat eigene Anforderungen. Der frühere Name `kuendigungsbutton_confirm_label` vermischte das erste und das dritte Element und ist deshalb entfallen.
>
> Besonders wichtig ist `has_confirmation_button`: Bisher gab es nur die Beschriftung. Fehlte die Schaltfläche ganz, wäre nicht unterscheidbar gewesen zwischen „nicht vorhanden" und „vorhanden, aber ohne Beschriftung" — zwei rechtlich völlig verschiedene Aussagen.

> Die 🟡-Signale setzen voraus, dass wir die Kündigungsstrecke **anklicken**. Das ist ein eigener Pfad je Ziel und für Freitag geplant.
>
> **„gut lesbar" bleibt eine Wertung.** Es gibt kein Signal `button_is_clearly_legible`. Schriftgröße und Kontrast sind Indizien; die Bewertung nimmt die Regel vor.

---

## Preise — Ergänzungen

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `additional_costs_mentioned_on_product_page` | bool | 🟡 | Wird auf der Produktseite überhaupt erwähnt, **ob** zusätzliche Fracht-, Liefer- oder Versandkosten anfallen — unabhängig von der Höhe? § 6 Abs. 1 Nr. 2 PAngV verlangt diese Angabe auch dann, wenn die Höhe nicht im Voraus berechenbar ist. Angefordert von DK, 20.08.; von SW bestätigt |
| `shipping_cost_amount` | Zahl | ✅ | Betrag der auf der Produktseite genannten Versandkosten |
| `listed_price_components` | Liste | ✅ | die auf der Produktseite ausgewiesenen Preisbestandteile mit Bezeichnung und Betrag (Grundpreis, Versand, Gebühren …) — Grundlage für § 3 PAngV |
| `gratis_claim_scope` | Text | ✅ | Text im Umfeld des Gratis-Versprechens |
| `free_pickup_option_present` | bool | ✅ | kostenlose Abholung wählbar — beobachtbarer Anhaltspunkt für die Ausnahme des Anhangs Nr. 20 |
| `vat_disclosure_present` | bool | ✅ | Hinweis auf die Umsatzsteuer im Preisumfeld — **hochgestuft von ⚪** |
| `vat_disclosure_scroll_pct` | Zahl | ✅ | Position dieses Hinweises — misst „versteckt in der Kopf-/Fußzeile" |

---

## Verdeckung von Informationen — Ergänzung

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `required_info_type` | Text | ✅ | welches Stichwort gegriffen hat (`Widerruf`, `Impressum`, `Gesamtpreis` …) |

---

## Umbenennungen — bitte die vorhandenen Namen verwenden

Diese Signale wurden gewünscht, existieren aber bereits unter anderem Namen:

| gewünscht | **bitte verwenden** |
|---|---|
| `is_consumer_offer`, `is_consumer_contract` | `is_b2c_offer` |
| `listed_total_price` | `price_listed` |
| `shipping_cost_disclosed` | `shipping_cost_disclosed_on_product_page` |
| `contract_concludable_on_website`, `is_electronic_business_transaction` | `order_button_found` + `has_checkout_flow` |
| `entrepreneur_owes_paid_performance` | `has_price_display` + `order_button_found` |
| `subscription_keyword_present` | `has_recurring_contract_keywords` |

## Entfallen — durch die Pfaderfassung bereits erfüllt

`first_price_display_timestamp` · `additional_cost_first_display_timestamp` · `price_history_within_current_journey`

Seit dem 19.08. führt **jedes** Signal mit, auf welchem Schritt es gemessen wurde (`schritt`) und welcher Screenshot es belegt. Wann eine Angabe erstmals erschien, ergibt sich daraus unmittelbar. Bitte stattdessen im Bericht auf `{schritt}` verweisen.

## Nicht als Signal — gehört nach `menschliche_pruefung`

Diese Merkmale sind **rechtliche Wertungen** und werden es auch bis Sonntag nicht:

| Merkmal | warum |
|---|---|
| `stricter_form_required` | erfordert Kenntnis des konkreten Vertragstyps |
| `costs_are_unavoidable_delivery_or_offer_costs` | Ausnahme des Anhangs Nr. 20 — Wertung. Beobachtbarer Anhaltspunkt: `free_pickup_option_present` |
| `required_total_price_can_be_calculated` | „vernünftigerweise im Voraus berechenbar" ist ein Rechtsbegriff |
| `shipping_cost_can_be_calculated_in_advance` | dito |
| `kuendigungsbutton_label_is_not_clearly_equivalent` | „entsprechend eindeutig" ist Auslegung — **stattdessen** `kuendigungsbutton_label` gegen eine Positiv-/Negativliste prüfen, siehe `_VORLAGE.yaml` |
| „spürbare Beeinträchtigung" (§ 3a UWG) | reine Wertung, taucht als Signal gar nicht erst auf |

### Kein eigenes Signal, weil in der Regel ausdrückbar

`costs_present_despite_gratis_claim` ist kein Messwert, sondern eine **Verknüpfung zweier Messwerte**. Genau dafür ist `verdict_rules` da:

```yaml
  - condition: "gratis_claim_present == true and shipping_cost_amount > 0"
```

Grundsatz: Das System misst Tatsachen, die Regel verknüpft sie. Ein Signal, das bereits eine Schlussfolgerung enthält, verschiebt die Verknüpfung in den Code — dorthin, wo das juristische Team sie nicht mehr ändern kann.

*Ob die Kosten sich überhaupt auf das als „gratis" beworbene Angebot beziehen, bleibt zudem eine Wertung. Beobachtbarer Anhaltspunkt für die Ausnahme des Anhangs Nr. 20: `free_pickup_option_present`.*

## Zurückgestellt mit DP-005b

Alle Signale, die eine Navigation **bis zur Kasse** voraussetzen, bleiben ⚪ und werden nur gebaut, wenn nach dem Feature Freeze am Samstag noch Zeit ist:

`mandatory_total_price_at_checkout` · `optional_costs_at_checkout` · `price_immediately_before_order` · `mandatory_price_delta` · `optional_price_delta` · `additional_mandatory_cost_count` · `additional_mandatory_cost_amount` · `additional_mandatory_cost_disclosed` · `additional_mandatory_cost_disclosed_before_order` · `additional_mandatory_cost_first_display_after_product_page` · `paid_addon_disclosed_before_selection` · `preselected_paid_addon_amount` · `additional_search_step_required` · `regular_login_required_for_service` · `required_info_visible_before_purchase_decision` · `shipping_cost_disclosed_before_checkout`

**Bitte keine Regel bauen, deren Kern auf diesen Signalen steht.** DP-005a kommt ohne sie aus.

---

## Wo gemessen wird — Pfaderfassung

**Neu seit 19.08.** Die Verbraucherzentrale hat im Seminar darauf hingewiesen, dass die interessanten Muster **nicht auf der Startseite** stehen: „so viele Nutzer haben sich das Produkt zuletzt angeschaut" erscheint erst, wenn man das Produkt anklickt; dasselbe gilt für die Mehrwertsteuer-Angabe und für Gebühren.

Das System ruft deshalb nicht eine URL auf, sondern arbeitet je Ziel einen **Pfad** ab:

```
startseite → suchergebnis → produktdetail → warenkorb → bestelluebersicht
```

Jedes gemessene Signal führt mit, **auf welchem Schritt** es erhoben wurde und **welcher Screenshot** es belegt. Für euch ändert sich dadurch nichts an der Schreibweise der Regeln — ihr benutzt die Signalnamen wie bisher. Es bedeutet aber:

- Ein Signal kann auf einem Schritt vorhanden und auf einem anderen nicht erhoben worden sein.
- Bricht der Pfad ab (Seite nicht erreichbar, Schaltfläche nicht gefunden), landen die restlichen Signale in `signal_errors` und die davon abhängigen Regeln werden automatisch `unklar`.

Wenn für eure Regel wichtig ist, **auf welchem Schritt** gemessen wurde, schreibt das bitte in `offene_fragen` — dann bauen wir es als eigenes Signal.

---

## Kontext und Anwendbarkeit

Diese Signale werden nicht bewertet, sondern in `applies_when` benutzt, um zu entscheiden, ob eine Regel überhaupt greift.

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `is_b2c_offer` | bool | ✅ | Richtet sich das Angebot an Verbraucher? (Heuristik über Preisangaben inkl. MwSt.) |
| `has_recurring_contract_keywords` | bool | ✅ | Hinweise auf Dauerschuldverhältnis: `Abo`, `Mitgliedschaft`, `Tarif`, `monatlich`, `Vertragslaufzeit` |
| `has_checkout_flow` | bool | ✅ | Existiert überhaupt ein Bestellvorgang? |
| `page_language` | Text | ✅ | Sprachkennung der Seite |

---

## Immer mitgeführte Nachweisdaten

Diese Felder erscheinen automatisch in jedem Bericht. Ihr müsst sie nicht angeben.

| Feld | Bedeutung |
|---|---|
| `screenshot` | Bildschirmaufnahme zum Zeitpunkt der Erfassung |
| `dom_hash` | Prüfsumme des Seitenzustands – belegt, dass die Seite später verändert wurde |
| `timestamp` | Datum und Uhrzeit der Erfassung |
| `viewport` | verwendete Fenstergröße (wichtig für die Reproduzierbarkeit von Flächenangaben) |
| `user_agent` | Browserkennung |
| `capture_mode` | `headless` oder `browser_extension` |
| `schritt` | auf welchem Schritt des Pfades der Wert erhoben wurde |
| `branche` | Branche des Ziels (Ticketing, Reise, Mode …) — Grundlage der Statistik in der Marktübersicht |

---

## Ein Signal fehlt euch?

Meldet euch **vor** dem Schreiben der Regel im Teamchat mit:

1. Was soll gemessen werden?
2. Für welches Tatbestandsmerkmal wird es gebraucht?
3. Ginge es notfalls auch mit einem vorhandenen Signal näherungsweise?

Das Entwicklungsteam sagt dann zu oder ab. Eine Zusage bedeutet Status 🟡. Bitte baut keine Regel, deren Kern auf einem noch nicht zugesagten Signal steht.
