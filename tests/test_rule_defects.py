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


print("DP-002 — the greylist was unreachable, and the whitelist was closed")
# T4 (BEFUNDSTUFEN): § 312j Abs. 3 S. 2 BGB allows "eine entsprechend
# eindeutige Formulierung", so no finite whitelist can prove the negative.
# "eindeutig" now comes only from the negative list — labels with no
# reference to payment at all.
# Every greylist entry is also absent from the whitelist, and "eindeutig" is
# evaluated first. A shop using the disputed "Jetzt bestellen" was reported
# as a clear violation.
base = dict(confirmed=["is_b2c_offer"], is_b2c_offer=True,
            has_checkout_flow=True, order_button_found=True,
            has_price_display=True, is_financial_services=False)
for label, expected in [("Jetzt bestellen", "verdaechtig"),
                        ("Bestellung abschließen", "verdaechtig"),
                        ("Weiter", "eindeutig"),
                        ("Jetzt anmelden", "eindeutig"),
                        ("Zahlungspflichtig buchen", "unauffaellig"),
                        ("Kostenpflichtig abonnieren", "unauffaellig"),
                        ("zahlungspflichtig bestellen", "unauffaellig")]:
    got = assess(RULES["DP-002"], table(order_button_label=label, **base)).level
    assert got == expected, f"{label!r} -> {got}, expected {expected}"
    print(f"  ok  {label!r} -> {expected}")

print("DP-002 — wording, not typography (EuGH C-249/21)")
for label in ("Jetzt kaufen!", "  KAUFEN  ", "kaufen."):
    got = assess(RULES["DP-002"], table(order_button_label=label, **base)).level
    assert got == "unauffaellig", f"{label!r} -> {got}"
    print(f"  ok  {label!r} is the same wording")

print("DP-001 — a cookie count cannot carry eindeutig at all (T2)")
# § 25 Abs. 2 TDDDG exempts technically necessary storage, and a counter
# cannot tell it from tracking — an embedded map, a font, a reCAPTCHA. While
# the exception is open, the strongest level is locked.
banner = dict(banner_detected=True, preselected_checkbox_count=0,
              reject_button_present=True, reject_click_depth=1,
              accept_button_area_px2=1000, reject_button_area_px2=980,
              accept_contrast_ratio=7.0, reject_contrast_ratio=6.9,
              banner_reappears_count_24h=0, banner_reappears_on_reject=False,
              more_info_present=False, more_info_leads_to_reject=True,
              more_info_click_depth=1)
for count in (1, 2, 7):
    got = level("DP-001", third_party_cookies_before_consent=count, **banner)
    assert got == "verdaechtig", f"{count} cookies -> {got}"
    print(f"  ok  {count} cookie(s) -> verdaechtig, never eindeutig")
assert level("DP-001", third_party_cookies_before_consent=0, **banner) == "unauffaellig"
print("  ok  none -> no finding")

print("DP-001 — the one condition that does carry eindeutig")
no_refusal = {**banner, "third_party_cookies_before_consent": 0,
              "reject_button_present": False, "more_info_leads_to_reject": False}
assert level("DP-001", **no_refusal) == "eindeutig"
print("  ok  banner with no way to refuse -> eindeutig (OLG Köln 6 U 80/23)")

print("DP-001 — a preselected control is not a clear violation either")
assert level("DP-001", **{**banner, "third_party_cookies_before_consent": 0,
                          "preselected_checkbox_count": 2}) == "verdaechtig"
print("  ok  the locked 'Notwendig' toggle of every CMP stays verdaechtig")

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
info = dict(confirmed=["is_b2c_offer"], is_b2c_offer=True, has_price_display=True,
            order_button_found=True, required_info_found=True,
            required_info_type="Widerruf", hidden_by_opacity_count=0,
            required_info_in_collapsed_element=False,
            aria_hidden_on_required_info=False)
# Five real German footers. Scroll depth is no longer part of any verdict:
# a mandatory notice in the footer is below 75% by definition, so it added
# nothing to a pair and turned both pairs back into the single conditions
# they were meant to replace.
for name, px, contrast, depth in [("Modeshop", 11, 4.54, 92), ("Bank", 10, 3.5, 88),
                                  ("Nachrichten", 12, 2.85, 95), ("Baeckerei", 11, 4.68, 90),
                                  ("Behoerde", 14, 3.1, 85)]:
    got = level("DP-006", font_size_min_px=px, text_contrast_min=contrast,
                scroll_depth_of_required_info_pct=depth, **info)
    assert got == "unauffaellig", f"{name} ({px}px/{contrast}) -> {got}"
    print(f"  ok  {name}: {px}px / {contrast} / {depth}% -> no finding")
assert level("DP-006", font_size_min_px=8, text_contrast_min=2.0,
             scroll_depth_of_required_info_pct=90, **info) == "verdaechtig"
print("  ok  8px AND contrast 2.0 -> verdaechtig")
assert level("DP-006", font_size_min_px=8, text_contrast_min=2.0,
             scroll_depth_of_required_info_pct=90,
             **{**info, "required_info_type": "Impressum"}) == "unauffaellig"
print("  ok  a tiny Impressum in the footer is the place § 5 DDG contemplates")

print("DP-006 — the worst case no longer disappears")
# "required_info_found == true" used to sit in applies_when, so a site that
# hides the mandatory information entirely dropped out of the report.
missing = {**info, "required_info_found": False,
           "font_size_min_px": 14, "text_contrast_min": 7.0,
           "scroll_depth_of_required_info_pct": 40}
# Landed on "unklar" on 20.08.: we search by keyword over three or four pages,
# and § 5a Abs. 3 Nr. 2 UWG requires other ways of providing the information
# to be taken into account. "unklar" is reportable, so the worst case still
# appears in the evidence file — which was the worry behind the first fix.
assert level("DP-006", **missing) == "unklar"
print("  ok  mandatory information not findable -> unklar, still reported")

print("DP-004 — applicability now rests on measurable facts")
# Tightened on 20.08.: a periodic price notation alone matches financing
# widgets ("ab 9,99 €/Monat") on ordinary one-off shops. It now has to be
# accompanied by a second indicator.
shop = dict(confirmed=["is_b2c_offer"], is_b2c_offer=True, order_button_found=True,
            has_price_display=True, is_financial_services=False,
            recurring_price_notation_present=True, min_contract_term_stated=False,
            auto_renewal_text_present=True, cancellation_terms_present=False,
            has_recurring_contract_keywords=False)
finding = assess(RULES["DP-004"], table(has_kuendigungsbutton=False, **shop))
assert finding.level == "verdaechtig", finding.level
print("  ok  subscription shop without a cancellation button -> verdaechtig")

# Two independent reasons keep this off "eindeutig": the condition itself was
# moved down under T3 (we only visited a few pages), and the rule declares
# applicability_derived, which caps it regardless. Check the cap really works
# by testing the one condition that DOES sit at eindeutig.
reached = assess(RULES["DP-004"], table(
    has_kuendigungsbutton=True, has_confirmation_page=True,
    has_confirmation_button=False, **shop))
assert reached.level == "verdaechtig" and reached.downgraded, reached.level
assert "abgeleitet" in " ".join(reached.notes)
assert "confirmed_by_human" not in " ".join(reached.notes), \
    "the note must not promise a lift that applicability_derived cannot give"
print("  ok  C4 caps the eindeutig condition, and says so truthfully")

single = {**shop, "recurring_price_notation_present": True,
          "auto_renewal_text_present": False}
assert assess(RULES["DP-004"], table(has_kuendigungsbutton=False, **single)).level \
    == "nicht_anwendbar"
print("  ok  financing notation alone -> rule does not apply")

print("\nDP-001 — a site with no banner at all no longer disappears")
# "banner_detected == true" used to gate the whole rule, so the gravest case
# — no consent mechanism at all, yet third-party cookies — dropped out.
no_banner = assess(RULES["DP-001"],
                   table(banner_detected=False, third_party_cookies_before_consent=7))
assert no_banner.level == "verdaechtig", no_banner.level
print("  ok  no banner + tracking -> verdaechtig, and the rule still applies")

quiet = assess(RULES["DP-001"],
               table(banner_detected=False, third_party_cookies_before_consent=0))
assert quiet.level == "nicht_anwendbar", quiet.level
print("  ok  no banner and no tracking -> rule does not apply")

# And no banner-design condition may fire on a page that has no banner:
# without one, "no reject button" is not a design decision.
finding = assess(RULES["DP-001"], table(
    banner_detected=False, third_party_cookies_before_consent=1,
    reject_button_present=False, more_info_leads_to_reject=False,
    reject_click_depth=4, preselected_checkbox_count=1))
assert finding.condition == "third_party_cookies_before_consent > 0", finding.condition
print("  ok  only the cookie branch fires when there is no banner")

print("\nDP-005 — shipping costs fall under the statutory exception")
# Anhang Nr. 20 to § 3 (3) UWG, second half-sentence: costs that are
# unavoidable for collection or delivery of the goods are exempt. Shipping
# costs are exactly that. Asserting "eindeutig" where the statute carves out
# an exception is a false alarm.
shop5 = dict(confirmed=["is_b2c_offer"], is_b2c_offer=True, has_price_display=True,
             has_checkout_flow=True, is_financial_services=False,
             vat_disclosure_present=True, preselected_paid_addon_count=0,
             gratis_claim_present=True, shipping_cost_amount=4.95,
             gratis_claim_scope="Gratis zum Bestellwert")

gratis = assess(RULES["DP-005"], table(free_pickup_option_present=False, **shop5))
assert gratis.level == "verdaechtig", gratis.level
assert "unvermeidbar" in (gratis.reason or ""), gratis.reason
print("  ok  gratis claim + shipping costs, no pickup -> verdaechtig, exception named")

# Narrowed on 21.08. Anhang Nr. 20 exempts costs unavoidable for collection
# or delivery. Where free pickup IS offered, they are avoidable and the
# exemption does not apply — but the far more common case is that the "free"
# promise simply is not about the goods the shipping is charged for.
assert assess(RULES["DP-005"], table(free_pickup_option_present=True, **shop5)
              ).level == "unauffaellig"
print("  ok  free pickup offered -> no finding")
for scope in ("Gratis Rücksendung", "Versandkostenfrei ab", "Gratis Abholung"):
    got = assess(RULES["DP-005"], table(
        **{**shop5, "free_pickup_option_present": False, "gratis_claim_scope": scope})).level
    assert got == "unauffaellig", f"{scope!r} -> {got}"
    print(f"  ok  {scope!r} is not about the goods -> no finding")

assert any("Abholung" in q for q in RULES["DP-005"].human_review), \
    "the unavoidability question must go to a human"
print("  ok  unavoidability is put to a human, not guessed")

print("\nDP-005 — the missing VAT notice, asked for by the agency itself")
vat = assess(RULES["DP-005"], table(
    **{**shop5, "vat_disclosure_present": False, "gratis_claim_present": False,
       "free_pickup_option_present": True}))
assert vat.level == "verdaechtig" and "Umsatzsteuer" in (vat.reason or ""), vat.level
print("  ok  no VAT notice in the price area -> verdaechtig (§ 6 Abs. 1 Nr. 1 PAngV)")
assert not RULES["DP-005"].verdict_rules["eindeutig"], \
    "DP-005 hat wieder einen eindeutig-Zweig — bitte gegen T1/T2/T3 pruefen"
print("  ok  DP-005 carries no eindeutig branch")

print("\nAll rule-defect guards passed.")
