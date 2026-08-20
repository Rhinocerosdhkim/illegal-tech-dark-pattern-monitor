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

print("Rechnungen")
pruefe("faktor ueber 2", "accept_button_area_px2 / reject_button_area_px2 > 2.0", True,
       accept_button_area_px2=4200, reject_button_area_px2=900)
pruefe("faktor unter 2", "accept_button_area_px2 / reject_button_area_px2 > 2.0", False,
       accept_button_area_px2=1000, reject_button_area_px2=900)
# Aus dem Briefing 3.4: "Ablehnung visuell zurueckgesetzt -> Kontrastdifferenz > 3.0".
# Ohne Subtraktion fiel diese Bedingung stillschweigend als Regelwerksfehler aus.
pruefe("kontrastdifferenz ueber 3", "accept_contrast_ratio - reject_contrast_ratio > 3.0", True,
       accept_contrast_ratio=8.4, reject_contrast_ratio=2.1)
pruefe("kontrastdifferenz unter 3", "accept_contrast_ratio - reject_contrast_ratio > 3.0", False,
       accept_contrast_ratio=7.1, reject_contrast_ratio=6.8)

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
                          ("banner_detected > true", "Zahlen")]:
    try:
        auswerten(kaputt, tabelle(banner_detected=True, a=True, b=True))
        raise AssertionError(f"kein Fehler bei {kaputt!r}")
    except RuleSyntaxError as fehler:
        assert stichwort in str(fehler), fehler
        print(f"  ok  {kaputt!r}")

# --- Nachtrag: was rules/_VORLAGE.yaml dem juristischen Team zusagt -------

print("\nOder-Verknuepfung (_VORLAGE.yaml: Operatoren ... and or)")
pruefe("oder, erstes wahr",  "a == true or b == true", True,  a=True,  b=False)
pruefe("oder, zweites wahr", "a == true or b == true", True,  a=False, b=True)
pruefe("oder, keines",       "a == true or b == true", False, a=False, b=False)
pruefe("and bindet staerker", "a == true and b == true or c == true", True,
       a=False, b=False, c=True)

print("Benannte Listen (_VORLAGE.yaml: listen:)")
LISTEN = {"zulaessige_labels": ["Verträge hier kündigen", "Vertrag hier kündigen"]}
for bedingung, erwartet, label in [
        ("kuendigungsbutton_label not in zulaessige_labels", True,  "Mein Konto"),
        ("kuendigungsbutton_label not in zulaessige_labels", False, "Verträge hier kündigen"),
        ("kuendigungsbutton_label in zulaessige_labels",     True,  "vertrag hier kündigen")]:
    got = auswerten(bedingung, tabelle(kuendigungsbutton_label=label), LISTEN).wahr
    assert got is erwartet, f"{bedingung!r} mit {label!r} -> {got}"
    print(f"  ok  {label!r}")

try:
    auswerten("kuendigungsbutton_label not in gibt_es_nicht",
              tabelle(kuendigungsbutton_label="x"), LISTEN)
    raise AssertionError("kein Fehler bei unbekannter Liste")
except RuleSyntaxError as fehler:
    assert "listen:" in str(fehler)
    print("  ok  unbekannte Liste wird benannt, nicht verschluckt")

print("Dreiwertige Logik — ein fehlendes Signal blockiert nicht mehr als noetig")
t = Signaltabelle(werte={"a": {"wert": False, "schritt": "s", "nachweis": "S-01.png"}},
                  fehler={"b": "nicht erhoben"})
assert auswerten("a == true and b == true", t).wahr is False
print("  ok  'and' ist falsch, sobald ein Glied falsch ist")
t2 = Signaltabelle(werte={"a": {"wert": True, "schritt": "s", "nachweis": "S-01.png"}},
                   fehler={"b": "nicht erhoben"})
assert auswerten("a == true or b == true", t2).wahr is True
print("  ok  'or' ist wahr, sobald ein Glied wahr ist")
for bedingung, tab in [("a == true and b == true", t2), ("a == true or b == true", t)]:
    try:
        auswerten(bedingung, tab)
        raise AssertionError(f"MissingSignal fehlt bei {bedingung!r}")
    except MissingSignal:
        pass
print("  ok  MissingSignal nur, wenn das Ergebnis wirklich davon abhaengt")

print("\nAlle Parsertests bestanden.")
