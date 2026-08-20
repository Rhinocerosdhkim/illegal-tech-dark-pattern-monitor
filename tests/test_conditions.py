"""The parser is where a silent error would be most expensive: a wrongly
evaluated comparison produces a false alarm against a real company. So the
tests come first, then everything else.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.conditions import (
    SignalTable, evaluate, MissingSignal, RuleSyntaxError)


def table(**values):
    return SignalTable(
        values={k: {"value": v, "step": "startseite", "evidence": "S-01.png"}
                for k, v in values.items()})


def check(name, condition, expected, **values):
    got = evaluate(condition, table(**values)).is_true
    assert got is expected, f"{name}: {condition!r} -> {got}, expected {expected}"
    print(f"  ok  {name}")


print("Comparisons")
check("equals true",   "banner_detected == true",             True,  banner_detected=True)
check("equals false",  "reject_button_present == false",      True,  reject_button_present=False)
check("not equal",     "countdown_resets_on_revisit != true", True,  countdown_resets_on_revisit=False)
check("greater",       "preselected_checkbox_count > 0",      True,  preselected_checkbox_count=1)
check("not greater",   "preselected_checkbox_count > 0",      False, preselected_checkbox_count=0)
check("greater equal", "banner_reappears_count_24h >= 2",     True,  banner_reappears_count_24h=2)
check("less",          "font_size_min_px < 12",               True,  font_size_min_px=11)

print("Arithmetic")
check("ratio above 2", "accept_button_area_px2 / reject_button_area_px2 > 2.0", True,
      accept_button_area_px2=4200, reject_button_area_px2=900)
check("ratio below 2", "accept_button_area_px2 / reject_button_area_px2 > 2.0", False,
      accept_button_area_px2=1000, reject_button_area_px2=900)
# From the briefing 3.4: "refusal visually de-emphasised -> contrast difference > 3.0".
# Without subtraction this condition silently dropped out as a rulebook error.
check("contrast diff above 3", "accept_contrast_ratio - reject_contrast_ratio > 3.0", True,
      accept_contrast_ratio=8.4, reject_contrast_ratio=2.1)
check("contrast diff below 3", "accept_contrast_ratio - reject_contrast_ratio > 3.0", False,
      accept_contrast_ratio=7.1, reject_contrast_ratio=6.8)

print("Conjunction")
check("both true", "countdown_element_present == true and countdown_resets_on_revisit == true",
      True, countdown_element_present=True, countdown_resets_on_revisit=True)
check("one false", "countdown_element_present == true and countdown_resets_on_revisit == true",
      False, countdown_element_present=True, countdown_resets_on_revisit=False)
check("three parts",
      "scarcity_text_present == true and scarcity_value > 0 and scarcity_value_unchanged_scans >= 3",
      True, scarcity_text_present=True, scarcity_value=3, scarcity_value_unchanged_scans=4)

print("Disjunction (_VORLAGE.yaml: operators ... and or)")
check("or, first true",  "a == true or b == true", True,  a=True,  b=False)
check("or, second true", "a == true or b == true", True,  a=False, b=True)
check("or, neither",     "a == true or b == true", False, a=False, b=False)
check("and binds tighter", "a == true and b == true or c == true", True,
      a=False, b=False, c=True)

print("Inline lists (DP-002)")
WHITE = ('order_button_label not_in_whitelist ["zahlungspflichtig bestellen", '
         '"kostenpflichtig bestellen", "kaufen", "jetzt kaufen"]')
GREY = ('order_button_label in_greylist ["jetzt bestellen", '
        '"Bestellung abschließen", "verbindlich bestellen"]')
check("not on whitelist",   WHITE, True,  order_button_label="Jetzt bestellen")
check("on whitelist",       WHITE, False, order_button_label="zahlungspflichtig bestellen")
check("case-insensitive",   WHITE, False, order_button_label="Zahlungspflichtig Bestellen")
check("whitespace ignored", WHITE, False, order_button_label="  kaufen ")
check("on greylist",        GREY,  True,  order_button_label="Jetzt bestellen")

print("Named lists (_VORLAGE.yaml: listen:)")
LISTS = {"zulaessige_labels": ["Verträge hier kündigen", "Vertrag hier kündigen"]}
for condition, expected, label in [
        ("kuendigungsbutton_label not in zulaessige_labels", True,  "Mein Konto"),
        ("kuendigungsbutton_label not in zulaessige_labels", False, "Verträge hier kündigen"),
        ("kuendigungsbutton_label in zulaessige_labels",     True,  "vertrag hier kündigen")]:
    got = evaluate(condition, table(kuendigungsbutton_label=label), LISTS).is_true
    assert got is expected, f"{condition!r} with {label!r} -> {got}"
    print(f"  ok  {label!r}")

try:
    evaluate("kuendigungsbutton_label not in does_not_exist",
             table(kuendigungsbutton_label="x"), LISTS)
    raise AssertionError("no error for an unknown list")
except RuleSyntaxError as error:
    assert "listen:" in str(error)
    print("  ok  unknown list is named, not swallowed")

print("YAML folded-block spelling from DP-005")
check("quotes and line break",
      '"has_price_display == false\n   and has_checkout_flow == true"',
      True, has_price_display=False, has_checkout_flow=True)

print("A missing signal is not swallowed")
try:
    evaluate("price_at_checkout > 0",
             SignalTable(values={}, errors={"price_at_checkout": "checkout unreachable"}))
    raise AssertionError("MissingSignal was not raised")
except MissingSignal as error:
    assert error.name == "price_at_checkout" and "checkout" in error.reason
    print("  ok  reported measurement problem")
try:
    evaluate("does_not_exist == true", SignalTable(values={}))
    raise AssertionError("MissingSignal was not raised")
except MissingSignal:
    print("  ok  unknown signal")

print("Three-valued logic — a missing signal blocks no more than necessary")
t_false = SignalTable(values={"a": {"value": False, "step": "s", "evidence": "S-01.png"}},
                      errors={"b": "not captured"})
assert evaluate("a == true and b == true", t_false).is_true is False
print("  ok  'and' is false as soon as one part is false")
t_true = SignalTable(values={"a": {"value": True, "step": "s", "evidence": "S-01.png"}},
                     errors={"b": "not captured"})
assert evaluate("a == true or b == true", t_true).is_true is True
print("  ok  'or' is true as soon as one part is true")
for condition, tab in [("a == true and b == true", t_true),
                       ("a == true or b == true", t_false)]:
    try:
        evaluate(condition, tab)
        raise AssertionError(f"MissingSignal missing for {condition!r}")
    except MissingSignal:
        pass
print("  ok  MissingSignal only when the result really depends on it")

print("Signals used are carried along for evidence binding")
e = evaluate("accept_button_area_px2 / reject_button_area_px2 > 2.0",
             table(accept_button_area_px2=4200, reject_button_area_px2=900))
assert e.signals_used == ["accept_button_area_px2", "reject_button_area_px2"], e.signals_used
print("  ok  signal provenance")

print("Rulebook errors are named, not swallowed")
for broken, needle in [("banner_detected", "comparison operator"),
                       ("banner_detected > true", "numbers")]:
    try:
        evaluate(broken, table(banner_detected=True))
        raise AssertionError(f"no error for {broken!r}")
    except RuleSyntaxError as error:
        assert needle in str(error), error
        print(f"  ok  {broken!r}")

print("\nAll parser tests passed.")
