"""Was passiert, wenn die Erfassungsschicht etwas anderes liefert als vereinbart?

Ab Dienstag ist keine Entwicklung mehr verfuegbar. Ein Absturz ist dann
unbehebbar — eine Teilausgabe mit einer verstaendlichen Anmerkung nicht.
Deshalb muss jede Abweichung vom Vertrag zu einem Ergebnis fuehren, nicht
zu einem Stacktrace.
"""

import json, sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.lauf import lade_lauf
from dpm.engine.rules import lade_regelwerk
from dpm.engine.verdict import pruefe
from dpm.report.beweisakte import erzeuge

REGELN = lade_regelwerk()
GESUND = json.loads(pathlib.Path("data/fixtures/viagogo/capture.json").read_text())


def durchlauf(aenderung, name):
    roh = json.loads(json.dumps(GESUND))
    aenderung(roh)
    with tempfile.TemporaryDirectory() as tmp:
        ordner = pathlib.Path(tmp)
        (ordner / "capture.json").write_text(json.dumps(roh), encoding="utf-8")
        lauf = lade_lauf(ordner)
        befunde = [pruefe(r, lauf.tabelle) for r in REGELN]
        akte = erzeuge(lauf, befunde, ausgabe=ordner / "out", als_pdf=False)
        assert akte.html.exists(), f"{name}: keine Akte erzeugt"
        return lauf, befunde, akte.html.read_text(encoding="utf-8")


faelle = [
    ("blanker Signalwert statt {wert, schritt, nachweis}",
     lambda r: r["signals"].update({"banner_detected": True})),
    ("Signalwert null",
     lambda r: r["signals"].update({"banner_detected": {"wert": None, "schritt": "x"}})),
    ("kein viewport in meta",
     lambda r: r["meta"].pop("viewport")),
    ("kein timestamp, keine run_id",
     lambda r: [r["meta"].pop("timestamp"), r["meta"].pop("run_id")]),
    ("leere Signalliste",
     lambda r: r.update({"signals": {}})),
    ("keine Schritte",
     lambda r: r.update({"schritte": []})),
    ("Schritt ohne Bezeichnung",
     lambda r: r["schritte"].append({"url": "x"})),
    ("Schritt ist eine Zeichenkette",
     lambda r: r["schritte"].append("startseite")),
    ("Signal verweist auf unbekannten Schritt",
     lambda r: r["signals"]["banner_detected"].update({"schritt": "gibt-es-nicht"})),
    ("Zielname mit Pfadwechsel",
     lambda r: r["meta"].update({"ziel": "../../rules/DP-001_Consent-Buttons"})),
    ("run_id mit Schraegstrich",
     lambda r: r["meta"].update({"run_id": "../ausserhalb/lauf"})),
    ("nicht erhobene Signale fehlen ganz",
     lambda r: r.pop("signal_errors")),
]

for name, aenderung in faelle:
    lauf, befunde, html = durchlauf(aenderung, name)
    print(f"  ok  {name}")

print("\nDie Akte behauptet keinen Screenshot, den es nicht gibt")
lauf, befunde, html = durchlauf(lambda r: None, "gesund")
assert "nicht bei" in html or "S-01.png" in html
with tempfile.TemporaryDirectory() as tmp:
    ordner = pathlib.Path(tmp)
    (ordner / "capture.json").write_text(json.dumps(GESUND), encoding="utf-8")
    lauf = lade_lauf(ordner)                       # ohne die PNG-Dateien daneben
    befunde = [pruefe(r, lauf.tabelle) for r in REGELN]
    akte = erzeuge(lauf, befunde, ausgabe=ordner / "out", als_pdf=False)
    html = akte.html.read_text(encoding="utf-8")
    assert "<img" not in html, "Akte verweist auf ein Bild, das nicht existiert"
    assert "nicht bei" in html
print("  ok  fehlender Screenshot wird ausgewiesen statt verlinkt")

print("\nAusbruch aus dem Ausgabeordner")
lauf, _, _ = durchlauf(lambda r: r["meta"].update({"run_id": "../ausserhalb/lauf"}),
                       "run_id")
assert "/" not in lauf.run_id and not lauf.run_id.startswith("."), lauf.run_id
assert (pathlib.Path("out") / lauf.run_id).resolve().parent == pathlib.Path("out").resolve()
print(f"  ok  run_id entschaerft zu {lauf.run_id!r}")
lauf, _, _ = durchlauf(lambda r: r["meta"].update({"ziel": "../../rules/DP-001_Consent-Buttons"}),
                       "ziel")
assert lauf.ziel == {}, "fremde Datei als Zielprofil geladen"
print("  ok  Zielname mit Pfadwechsel laedt kein fremdes Profil")

print("\nWarnungen erreichen den Bericht")
lauf, _, html = durchlauf(lambda r: r["signals"].update({"banner_detected": True}),
                          "blanker Wert")
assert any("ohne Nachweis" in w for w in lauf.warnungen), lauf.warnungen
assert "ohne Nachweis" in html
print("  ok  Vertragsverletzung steht in der Akte, nicht nur im Terminal")

print("\nAlle Robustheitstests bestanden.")
