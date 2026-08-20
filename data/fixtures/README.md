# Fixtures — handgeschriebene Erfassungsläufe

Keine echten Messwerte. Zweck: die Auswertungsschicht (Regelwerk, Beweisakte,
Marktübersicht) entwickeln und prüfen, **ohne auf die Erfassungsschicht zu
warten** — und danach als Regressionstest dienen.

| Ordner | Was es darstellt | Erwartetes Ergebnis |
|---|---|---|
| `viagogo/` | Referenzfall, von der Verbraucherzentrale benannt | 3 × eindeutig, 3 × unklar |
| `sauberer-shop/` | unauffälliger Shop, korrekt gestaltet | kein Befund |
| `ratgeber-portal/` | redaktionelles Portal, kein Shop, kein Banner | Regeln greifen gar nicht |

**`sauberer-shop` und `ratgeber-portal` haben bewusst kein Zielprofil in
`data/targets/`.** Damit ist geprüft, dass ein beliebiges Ziel ohne
Handeinrichtung durch die gesamte Kette läuft — das Werkzeug soll für jede
Website taugen, nicht nur für die, die wir vorbereitet haben.

Die Folge ist sichtbar und gewollt: ohne menschliche Bestätigung im Zielprofil
(`bestaetigt_durch_mensch`) bleibt eine Regel, deren Anwendbarkeit auf einer
Ableitung beruht, auf `verdaechtig` begrenzt (C4).

Ändert sich ein Ergebnis, bricht `tests/test_befund.py` bzw.
`tests/test_unauffaellig.py`. Dann bitte hinsehen, nicht stillschweigend
den erwarteten Wert anpassen.
