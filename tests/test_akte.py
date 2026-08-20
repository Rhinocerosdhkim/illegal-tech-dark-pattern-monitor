"""Die Beweisakte ist das Dokument, das einer Abmahnung beiliegt. Ein
Sachfehler darin ist teurer als ein Absturz. Deshalb hier vor allem: steht
nur drin, was auch gemessen wurde?
"""

import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.lauf import lade_lauf
from dpm.engine.rules import lade_regelwerk
from dpm.engine.verdict import pruefe
from dpm.report.beweisakte import erzeuge

lauf = lade_lauf("data/fixtures/viagogo")
befunde = [pruefe(r, lauf.tabelle) for r in lade_regelwerk()]

with tempfile.TemporaryDirectory() as tmp:
    akte = erzeuge(lauf, befunde, ausgabe=tmp, als_pdf=False)
    html = akte.html.read_text(encoding="utf-8")

    assert akte.anzahl_befunde == 6, akte.anzahl_befunde
    print("  ok  6 berichtsrelevante Befunde")

    # Der entscheidende Test: kein gemessener Wert darf als "nicht erhoben"
    # ausgewiesen werden. Das waere eine falsche Tatsachenbehauptung.
    gemessen = {"accept_button_area_px2", "reject_click_depth",
                "preselected_checkbox_count", "third_party_cookies_before_consent"}
    assert gemessen <= set(lauf.tabelle.werte), "Fixture geaendert?"
    assert "[nicht erhoben]" not in html, \
        "Ein gemessener Wert wird als nicht erhoben ausgewiesen"
    print("  ok  kein gemessener Wert als 'nicht erhoben' ausgewiesen")

    for pflicht, name in [
            ("sha256:", "DOM-Hash"),
            ("Erfassungsbedingungen", "Reproduzierbarkeit"),
            ("Herkunft der Schwellenwerte", "threshold_source"),
            ("Fehlalarmrisiken", "false_positive_risks"),
            ("Anspruchskette", "Anspruchskette"),
            ("PLATZHALTER", "vorlaeufiger Hinweis (Paket 3 offen)"),
            ("Nicht erhoben", "Messluecken werden benannt"),
            ("S-01.png", "Screenshot eingebunden")]:
        assert pflicht in html, f"fehlt in der Akte: {name}"
        print(f"  ok  {name}")

    assert "Irrefuehrung" not in html, "Kategorie ohne Umlaut im Dokument"
    print("  ok  Kategorien in deutscher Schreibweise")

    for datei in ("S-01.png", "S-03.png"):
        assert (akte.html.parent / datei).exists(), f"{datei} nicht mitkopiert"
    print("  ok  Ausgabeordner ist in sich abgeschlossen")

print("\nAlle Aktentests bestanden.")
