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
| `kuendigungsbutton_confirm_label` | Text | 🟡 | Beschriftung auf der Bestätigungsseite |

---

## Dringlichkeit und Knappheit

| Signal | Typ | Status | Bedeutung |
|---|---|---|---|
| `countdown_element_present` | bool | ✅ | Ist ein Countdown auf der Seite? |
| `countdown_initial_value_sec` | Zahl | ✅ | Startwert in Sekunden beim ersten Aufruf |
| `countdown_resets_on_revisit` | bool | ✅ | **Springt der Countdown nach Löschen aller Browserdaten und erneutem Aufruf auf denselben Startwert zurück?** |
| `countdown_text` | Text | ✅ | umgebender Text im Wortlaut |
| `scarcity_text_present` | bool | ✅ | Knappheitshinweis vorhanden (z. B. „nur noch 2 verfügbar") |
| `scarcity_value` | Zahl | ✅ | die genannte Stückzahl |
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

---

## Ein Signal fehlt euch?

Meldet euch **vor** dem Schreiben der Regel im Teamchat mit:

1. Was soll gemessen werden?
2. Für welches Tatbestandsmerkmal wird es gebraucht?
3. Ginge es notfalls auch mit einem vorhandenen Signal näherungsweise?

Das Entwicklungsteam sagt dann zu oder ab. Eine Zusage bedeutet Status 🟡. Bitte baut keine Regel, deren Kern auf einem noch nicht zugesagten Signal steht.
