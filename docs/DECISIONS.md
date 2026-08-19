# Entscheidungslog

Jede inhaltliche Entscheidung mit **Datum, Entscheidung, Begründung**. Neueste oben.
Zweck: dieselbe Diskussion nicht zweimal führen — und Material für die Fragerunde nach der Präsentation.

Format: `## JJJJ-MM-TT — Entscheidung` + zwei bis vier Sätze Begründung. Kurz halten.

---

## 2026-08-19 — Positionierung: Bezahlbarkeit ist die Lücke, nicht Erkennung

Aus dem Seminar der Verbraucherzentrale Bayern: Die bestehenden Werkzeuge (FairPatterns, R Systems) scheitern nicht an Funktionen, sondern am Budget. Daraus folgt unsere geschärfte These: **„Dark Patterns zu erkennen können andere längst. Sie bezahlbar und abmahnfähig zu dokumentieren kann niemand."** Open Source und Selbstbetrieb sind damit kein Nebenaspekt, sondern das Kernargument.

## 2026-08-19 — Primäre Ausgabe ist die Prüftabelle, nicht der Fließtext

Die Verbraucherzentrale hat im Seminar ausdrücklich eine **Tabelle** genannt, aus der sich die Rechtsgrundlagen für eine Abmahnung entnehmen lassen. Die Tabelle wird deshalb bis Freitag gebaut und ist der Mittelpunkt der Demo — nicht das letzte Feature vor Schluss.

## 2026-08-19 — Headless zuerst, Chrome-Erweiterung als optionaler Aufsatz

Eine Extension allein kann das von der Challenge ausdrücklich verlangte **Monitoring über Zeit** nicht leisten, weil sie nur läuft, wenn ein Mensch die Seite besucht. Ebenso wenig den Countdown-Nachweis, der einen sauberen Browserzustand braucht. Gegenmaßnahme: Alle Signalmessungen werden als reines Browser-JavaScript ohne Playwright-Abhängigkeit geschrieben. Damit läuft dieselbe Datei später unverändert als Content Script — die Extension kostet dann nur noch Manifest und Popup.

## 2026-08-19 — Vier Muster statt sechs

DP-001 bis DP-004 werden fertig, DP-005 und DP-006 nur bei Restzeit. DP-005 setzt Navigation bis zum Bestellabschluss voraus, was nicht zuverlässig gelingt und einen ganzen Tag kostet.

## 2026-08-19 — Kein Code aus rajnish159/Dark-Pattern-Detection

Das Repository enthält **keine Lizenzangabe**; ohne Lizenz gilt das Urheberrecht vollumfänglich und eine Nachnutzung wäre unzulässig. Wir nutzen es allenfalls als Ideengeber und schreiben alles selbst.

## 2026-08-19 — Kein Machine Learning im Befund (bestätigt)

UIGuard (arXiv 2308.05898v2) erreicht Precision 0,83 — jeder sechste Befund ist falsch. Als Grundlage einer Abmahnung unbrauchbar. Wir nennen die Arbeit in der Präsentation als Stand der Forschung und als Beleg, dass wir die Alternative kennen und bewusst anders entschieden haben.

## 2026-08-19 — Art. 25 DSA wird kein eigenständiges Befundmuster

Art. 25 Abs. 2 DSA nimmt Sachverhalte aus, die bereits von der UGP-Richtlinie (umgesetzt im UWG) oder der DSGVO erfasst sind. Ein eigenständig behaupteter DSA-Verstoß wäre daher in vielen Fällen angreifbar. Wir nennen Art. 25 DSA in der Präsentation als übergreifenden Rahmen und als Ausblick — nicht als Grundlage unserer Befunde.

*Wer das juristisch mit Fundstellen vertiefen oder bestreiten möchte: sehr willkommen, das wäre ein starker Punkt in der Q&A.*

## 2026-08-19 — Regelwerk vom Code getrennt (`rules/*.yaml`)

Das juristische Team schreibt die Regeln, das Entwicklungsteam liest sie ein. Beide Teilteams können dadurch parallel arbeiten, ohne aufeinander zu warten. Zweiter Grund: Schwellenwerte lassen sich bis zuletzt anpassen, ohne dass jemand programmiert — genau das werden wir am Freitagabend beim Abgleich mit dem Gold Standard tun.

## 2026-08-19 — Kein Sprachmodell in der Befundentscheidung

Ein Modell wird nur an zwei Stellen eingesetzt: mehrdeutige Formulierungen deuten und den deutschen Berichtstext formulieren. Grund: Ein Befund, der auf einer Modellentscheidung beruht, ist weder reproduzierbar noch im Verfahren begründbar. Unsere Befunde müssen sich lückenlos zurückverfolgen lassen: gemessenes Signal → Bedingung im Regelwerk → Norm.

## 2026-08-19 — Dreistufiges Befundmodell, `unklar` als Qualitätsmerkmal

`eindeutig` / `verdächtig` / `unklar` / `unauffällig`. Die Stufe `unklar` vergibt das System automatisch, wenn ein benötigtes Signal nicht erhoben werden konnte. Sie ist kein Eingeständnis von Schwäche, sondern verhindert, dass wir behaupten, was wir nicht gemessen haben. Ein vorsichtiges System ist für eine Verbraucherzentrale brauchbar; ein übertreibendes ist es nicht — und macht uns selbst angreifbar (§ 4 Nr. 1, Nr. 2 UWG).

## 2026-08-19 — Sechs Muster gründlich statt zwanzig oberflächlich

DP-001 bis DP-006. Bei knapper Zeit entfallen DP-005 und DP-006 zuerst.
