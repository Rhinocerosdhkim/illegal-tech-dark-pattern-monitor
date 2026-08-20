"""Der Parser ist die Stelle, an der ein stiller Fehler am teuersten waere:
ein falsch ausgewerteter Vergleich erzeugt einen Fehlalarm gegen ein echtes
Unternehmen. Deshalb hier zuerst Tests, dann alles andere.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.conditions import (
    Signaltabelle, auswerten, MissingSignal, RuleSyntaxError)


def tabelle(**werte):
    return Signaltabelle(
        werte={k: {"wert": v, "schritt": "startseite", "nachweis": "S-01.png"}
               for k, v in werte.items()})


def pruefe(name, bedingung, erwartet, **werte):
    got = auswerten(bedingung, tabelle(**werte)).wahr
    assert got is erwartet, f"{name}: {bedingung!r} -> {got}, erwartet {erwartet}"
    print(f"  ok  {name}")


print("Vergleiche")
pruefe("gleich wahr",      "banner_detected == true",        True,  banner_detected=True)
pruefe("gleich falsch",    "reject_button_present == false", True,  reject_button_present=False)
pruefe("ungleich",         "countdown_resets_on_revisit != true", True, countdown_resets_on_revisit=False)
pruefe("groesser",         "preselected_checkbox_count > 0", True,  preselected_checkbox_count=1)
pruefe("groesser nicht",   "preselected_checkbox_count > 0", False, preselected_checkbox_count=0)
pruefe("groesser gleich",  "banner_reappears_count_24h >= 2", True, banner_reappears_count_24h=2)
pruefe("kleiner",          "font_size_min_px < 12",          True,  font_size_min_px=11)

print("Verhaeltnis")
pruefe("faktor ueber 2", "accept_button_area_px2 / reject_button_area_px2 > 2.0", True,
       accept_button_area_px2=4200, reject_button_area_px2=900)
pruefe("faktor unter 2", "accept_button_area_px2 / reject_button_area_px2 > 2.0", False,
       accept_button_area_px2=1000, reject_button_area_px2=900)

print("Und-Verknuepfung")
pruefe("beide wahr", "countdown_element_present == true and countdown_resets_on_revisit == true",
       True, countdown_element_present=True, countdown_resets_on_revisit=True)
pruefe("eine falsch", "countdown_element_present == true and countdown_resets_on_revisit == true",
       False, countdown_element_present=True, countdown_resets_on_revisit=False)
pruefe("drei Glieder",
       "scarcity_text_present == true and scarcity_value > 0 and scarcity_value_unchanged_scans >= 3",
       True, scarcity_text_present=True, scarcity_value=3, scarcity_value_unchanged_scans=4)

print("Listen (DP-002)")
WEISS = ('order_button_label not_in_whitelist ["zahlungspflichtig bestellen", '
         '"kostenpflichtig bestellen", "kaufen", "jetzt kaufen"]')
GRAU = ('order_button_label in_greylist ["jetzt bestellen", '
        '"Bestellung abschließen", "verbindlich bestellen"]')
pruefe("nicht auf Weissliste", WEISS, True,  order_button_label="Jetzt bestellen")
pruefe("auf Weissliste",       WEISS, False, order_button_label="zahlungspflichtig bestellen")
pruefe("Gross/Klein egal",     WEISS, False, order_button_label="Zahlungspflichtig Bestellen")
pruefe("Leerzeichen egal",     WEISS, False, order_button_label="  kaufen ")
pruefe("auf Graulistee",       GRAU,  True,  order_button_label="Jetzt bestellen")

print("Faltblock-Schreibweise aus DP-005")
pruefe("Anfuehrungszeichen und Umbruch",
       '"has_price_display == false\n   and has_checkout_flow == true"',
       True, has_price_display=False, has_checkout_flow=True)

print("Fehlendes Signal wird nicht verschluckt")
try:
    auswerten("price_at_checkout > 0",
              Signaltabelle(werte={}, fehler={"price_at_checkout": "Kasse nicht erreichbar"}))
    raise AssertionError("MissingSignal wurde nicht geworfen")
except MissingSignal as fehler:
    assert fehler.name == "price_at_checkout" and "Kasse" in fehler.grund
    print("  ok  gemeldetes Messproblem")
try:
    auswerten("gibt_es_nicht == true", Signaltabelle(werte={}))
    raise AssertionError("MissingSignal wurde nicht geworfen")
except MissingSignal as fehler:
    print("  ok  unbekanntes Signal")

print("Benutzte Signale werden fuer die Beweisbindung mitgefuehrt")
a = auswerten("accept_button_area_px2 / reject_button_area_px2 > 2.0",
              tabelle(accept_button_area_px2=4200, reject_button_area_px2=900))
assert a.benutzte_signale == ["accept_button_area_px2", "reject_button_area_px2"], a.benutzte_signale
print("  ok  Signalherkunft")

print("Regelwerksfehler werden benannt, nicht verschluckt")
for kaputt, stichwort in [("banner_detected", "Vergleichsoperator"),
                          ("a == true or b == true", "'or'"),
                          ("banner_detected > true", "Zahlen")]:
    try:
        auswerten(kaputt, tabelle(banner_detected=True, a=True, b=True))
        raise AssertionError(f"kein Fehler bei {kaputt!r}")
    except RuleSyntaxError as fehler:
        assert stichwort in str(fehler), fehler
        print(f"  ok  {kaputt!r}")

print("\nAlle Parsertests bestanden.")
