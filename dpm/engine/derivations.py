"""Which signals are findings of fact, and which are derivations?

This distinction carries C4 from docs/ABSTIMMUNG_Regelwerk.md:

    If applies_when rests on an *unconfirmed derivation*, the rule may
    reach at most "verdaechtig".

The word "unconfirmed" is what makes it workable. Without the list below
every prerequisite would count as a derivation — banner_detected included,
although that is a direct observation — and no rule could ever reach
"eindeutig".

Listed here is therefore only what ABSTIMMUNG_Regelwerk.md Korb C calls a
legal qualification or an explicit heuristic. Everything else counts as a
finding of fact.

The restriction can be lifted per target in data/targets/<name>.yaml:

    confirmed_by_human:
      is_b2c_offer: true      # checked: <initials>, <date>

OPEN: once _SIGNALE.md gains a column of its own for this, the file
disappears and provenance is read there. Until then this is the single
place where the distinction lives — not scattered through the code.
"""

DERIVED_SIGNALS = frozenset({
    # explicit heuristic per _SIGNALE.md
    "is_b2c_offer",
    "is_consumer_offer",        # another name for the same thing
    "is_consumer_contract",     # likewise

    # legal qualifications, derived from facts (Korb C)
    "is_dauerschuldverhaeltnis",
    "contract_concludable_on_website",
    "is_electronic_business_transaction",
    "entrepreneur_owes_paid_performance",
    "is_financial_services",
    "stricter_form_required",
    "costs_are_unavoidable_delivery_or_offer_costs",
    "required_total_price_can_be_calculated",
    "shipping_cost_can_be_calculated_in_advance",
    "kuendigungsbutton_label_is_not_clearly_equivalent",
    "button_is_clearly_legible",
})


def is_derived(signal_name: str) -> bool:
    return signal_name in DERIVED_SIGNALS
