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
| `pattern_id` | `DP-001` … `DP-006` |
| `befund_mensch` | `eindeutig` / `verdaechtig` / `unauffaellig` |
| `nachweis` | Dateiname des Screenshots, oder Link |
| `bearbeiter` | Kürzel |
| `datum` | JJJJ-MM-TT |
| `notiz` | Begründung in einem Satz — vor allem bei Grenzfällen |

Screenshots gehören in `data/gold-standard/screenshots/`. Dateiname: `<domain>_<pattern-id>.png`, z. B. `beispielshop-de_DP-003.png`.
