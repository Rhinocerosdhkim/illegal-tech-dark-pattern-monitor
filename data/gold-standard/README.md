# Paket 2 — Gold Standard

**Frist: Freitag, 21.08., 18:00 Uhr**

Rund **20 Webseiten, von Hand** gegen unser eigenes Regelwerk bewertet. Eintragen in [`gold-standard.csv`](gold-standard.csv) — im Browser über das Stift-Symbol, oder in Excel/Numbers öffnen und wieder als CSV speichern.

## Warum das zählt

Nur mit dieser Referenz können wir in der Präsentation eine belastbare Aussage zur Treffsicherheit machen. Ein Team mit einer nachvollziehbaren Messung überzeugt deutlich mehr als eines mit bloßer Vorführung.

Am Freitagnachmittag vergleichen wir Systembefund gegen Menschenbefund und erhalten die ersten Genauigkeitszahlen.

## Auswahlkriterien

- ohne Login erreichbar
- deutschsprachig
- **etwa die Hälfte sollen unauffällige Seiten sein**

Der letzte Punkt ist der wichtigste: Wir müssen messen, wie oft unser System **Fehlalarm** schlägt. Ein System, das überall Verstöße sieht, ist wertlos.

Das Entwicklungsteam liefert **Donnerstagvormittag eine vorgeprüfte Kandidatenliste**, damit ihr nur Seiten bewertet, die technisch überhaupt erfassbar sind.

## Spalten

| Spalte | Inhalt |
|---|---|
| `url` | vollständige Adresse der geprüften Seite |
| `branche` | **neu** — Ticketing, Reise, Mode, Telekommunikation, Möbel, Elektronik … |
| `pattern_id` | `DP-001` … `DP-006` |
| `kategorie` | **neu** — `Zeitdruck` / `Zwang` / `Hindernisse` / `Irreführung` |
| `befund_mensch` | `eindeutig` / `verdaechtig` / `unauffaellig` |
| `nachweis` | Dateiname des Screenshots, oder Link |
| `bearbeiter` | Kürzel |
| `datum` | JJJJ-MM-TT |
| `notiz` | Begründung in einem Satz — vor allem bei Grenzfällen |

> **Warum `branche` und `kategorie` dazugekommen sind:** Die Verbraucherzentrale hat im Seminar vom 19.08. ausdrücklich eine Tabelle mit **Filtermöglichkeit und Statistiken nach Branche und Art** verlangt. Ohne diese beiden Spalten gibt es keine Statistik — und der Gold Standard ist zugleich der Inhalt unserer Marktübersicht in der Demo. Bitte bei jeder Zeile ausfüllen.

**Ein Ziel ist ausdrücklich benannt worden: [viagogo](https://www.viagogo.de) (Ticketverkauf).** Diese Seite bitte zuerst und besonders sorgfältig bewerten — sie ist unser Referenzfall in der Vorführung.

Screenshots gehören in `data/gold-standard/screenshots/`. Dateiname: `<domain>_<pattern-id>.png`, z. B. `beispielshop-de_DP-003.png`.
