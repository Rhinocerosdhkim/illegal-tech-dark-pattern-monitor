"""Guards for the rulebook defects repaired on 20.08.

Each of these fired against real, lawful websites. A rule that reports a
violation where there is none does not just produce noise — under § 4
nos. 1 and 2 UWG it makes us attackable ourselves. So each repair gets a
test that fails if the condition creeps back.
"""

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.conditions import SignalTable
from dpm.engine.rules import load_rules
from dpm.engine.verdict import assess

RULES = {r.id: r for r in load_rules()}


def table(confirmed=(), **values):
    return SignalTable(
        values={k: {"value": v, "step": "startseite", "evidence": "S-01.png"}
                for k, v in values.items()},
        confirmed=set(confirmed))


def level(rule_id, **values):
    return assess(RULES[rule_id], table(**values)).level


print("DP-002 — the greylist was unreachable")
# Every greylist entry is also absent from the whitelist, and "eindeutig" is
# evaluated first. A shop using the disputed "Jetzt bestellen" was reported
# as a clear violation.
base = dict(confirmed=["is_b2c_offer"], is_b2c_offer=True,
            has_checkout_flow=True, order_button_found=True)
for label, expected in [("Jetzt bestellen", "verdaechtig"),
                        ("Bestellung abschließen", "verdaechtig"),
                        ("Kaffee kaufen jetzt sofort", "eindeutig"),
                        ("zahlungspflichtig bestellen", "unauffaellig")]:
    got = assess(RULES["DP-002"], table(order_button_label=label, **base)).level
    assert got == expected, f"{label!r} -> {got}, expected {expected}"
    print(f"  ok  {label!r} -> {expected}")

print("DP-002 — wording, not typography (EuGH C-249/21)")
for label in ("Jetzt kaufen!", "  KAUFEN  ", "kaufen."):
    got = assess(RULES["DP-002"], table(order_button_label=label, **base)).level
    assert got == "unauffaellig", f"{label!r} -> {got}"
    print(f"  ok  {label!r} is the same wording")

print("DP-001 — one third-party cookie is not a clear violation")
banner = dict(banner_detected=True, preselected_checkbox_count=0,
              reject_button_present=True, reject_click_depth=1,
              accept_button_area_px2=1000, reject_button_area_px2=980,
              accept_contrast_ratio=7.0, reject_contrast_ratio=6.9,
              banner_reappears_count_24h=0, banner_reappears_on_reject=False,
              more_info_present=False, more_info_leads_to_reject=True,
              more_info_click_depth=1)
assert level("DP-001", third_party_cookies_before_consent=1, **banner) == "verdaechtig"
print("  ok  exactly one cookie -> verdaechtig (its own false_positive_risks ask for review)")
assert level("DP-001", third_party_cookies_before_consent=2, **banner) == "eindeutig"
print("  ok  two or more -> eindeutig")
assert level("DP-001", third_party_cookies_before_consent=0, **banner) == "unauffaellig"
print("  ok  none -> no finding")

print("DP-003 — a countdown alone is no finding at any level")
# Two deletions on 20.08. plus PV's removal of the eindeutig branch the same
# evening. A resetting countdown only shows the timer is session-scoped;
# session and checkout timers reset identically, and the rule's own
# false_positive_risks want those excluded. Nothing in Anhang Nr. 7 is
# established by a reset alone.
clean = dict(confirmed=["is_b2c_offer"], is_b2c_offer=True,
             scarcity_text_present=False, scarcity_value=0,
             scarcity_value_unchanged_scans=1)
for resets in (False, True):
    got = level("DP-003", countdown_element_present=True,
                countdown_resets_on_revisit=resets, **clean)
    assert got == "unauffaellig", f"countdown resets={resets} -> {got}"
    print(f"  ok  countdown, resets={resets} -> no finding")
assert not RULES["DP-003"].verdict_rules["eindeutig"], \
    "DP-003 hat wieder einen eindeutig-Zweig — bitte gegen BEFUNDSTUFEN T1 pruefen"
print("  ok  DP-003 carries no eindeutig branch")

print("DP-006 — soft indicators only count in combination")
# Small print in a footer describes practically every website. Each of the
# three conditions contradicted its own threshold_source when standalone.
info = dict(confirmed=["is_b2c_offer"], is_b2c_offer=True,
            required_info_found=True, hidden_by_opacity_count=0,
            required_info_in_collapsed_element=False,
            aria_hidden_on_required_info=False,
            required_info_visible_before_purchase_decision=True)
assert level("DP-006", font_size_min_px=11, text_contrast_min=7.0,
             scroll_depth_of_required_info_pct=40, **info) == "unauffaellig"
print("  ok  small print alone -> no finding")
assert level("DP-006", font_size_min_px=14, text_contrast_min=7.0,
             scroll_depth_of_required_info_pct=95, **info) == "unauffaellig"
print("  ok  footer position alone -> no finding")
assert level("DP-006", font_size_min_px=11, text_contrast_min=3.0,
             scroll_depth_of_required_info_pct=40, **info) == "verdaechtig"
print("  ok  small AND low contrast -> verdaechtig")

print("DP-006 — the worst case no longer disappears")
# "required_info_found == true" used to sit in applies_when, so a site that
# hides the mandatory information entirely dropped out of the report.
missing = {**info, "required_info_found": False,
           "font_size_min_px": 14, "text_contrast_min": 7.0,
           "scroll_depth_of_required_info_pct": 40}
assert level("DP-006", **missing) == "verdaechtig"
print("  ok  mandatory information not findable -> verdaechtig, not dropped")

print("DP-004 — applicability now rests on measurable facts")
shop = dict(confirmed=["is_b2c_offer"], is_b2c_offer=True, order_button_found=True,
            has_price_display=True, is_financial_services=False,
            recurring_price_notation_present=True, min_contract_term_stated=False,
            auto_renewal_text_present=False)
finding = assess(RULES["DP-004"], table(has_kuendigungsbutton=False, **shop))
assert finding.level == "verdaechtig", finding.level
assert finding.downgraded, "C4: a derived Dauerschuldverhaeltnis must cap the level"
print("  ok  subscription shop without a cancellation button -> verdaechtig (C4 cap)")

single = {**shop, "recurring_price_notation_present": False}
assert assess(RULES["DP-004"], table(has_kuendigungsbutton=False, **single)).level \
    == "nicht_anwendbar"
print("  ok  one-off purchase, no recurring signals -> rule does not apply")

print("\nDP-001 — a site with no banner at all no longer disappears")
# "banner_detected == true" used to gate the whole rule, so the gravest case
# — no consent mechanism at all, yet third-party cookies — dropped out.
no_banner = assess(RULES["DP-001"],
                   table(banner_detected=False, third_party_cookies_before_consent=7))
assert no_banner.level == "eindeutig", no_banner.level
print("  ok  no banner + tracking -> eindeutig (§ 25 Abs. 1 TDDDG)")

quiet = assess(RULES["DP-001"],
               table(banner_detected=False, third_party_cookies_before_consent=0))
assert quiet.level == "nicht_anwendbar", quiet.level
print("  ok  no banner and no tracking -> rule does not apply")

# And the button conditions must not fire on a page that has no banner.
assert assess(RULES["DP-001"], table(
    banner_detected=False, third_party_cookies_before_consent=1,
    reject_button_present=False, more_info_leads_to_reject=False)
).condition.startswith("banner_detected == false"), \
    "a button condition fired on a page without a banner"
print("  ok  button conditions stay bound to an existing banner")

print("\nDP-005 — shipping costs fall under the statutory exception")
# Anhang Nr. 20 to § 3 (3) UWG, second half-sentence: costs that are
# unavoidable for collection or delivery of the goods are exempt. Shipping
# costs are exactly that. Asserting "eindeutig" where the statute carves out
# an exception is a false alarm.
gratis = assess(RULES["DP-005"], table(
    confirmed=["is_b2c_offer"], is_b2c_offer=True, has_price_display=True,
    has_checkout_flow=True, is_financial_services=False,
    gratis_claim_present=True, shipping_cost_amount=4.95))
assert gratis.level == "verdaechtig", gratis.level
assert "unvermeidbar" in (gratis.reason or ""), gratis.reason
print("  ok  gratis claim + shipping costs -> verdaechtig, exception named")
assert any("Abholung" in q for q in RULES["DP-005"].human_review), \
    "the unavoidability question must go to a human"
print("  ok  unavoidability is put to a human, not guessed")

print("\nAll rule-defect guards passed.")
