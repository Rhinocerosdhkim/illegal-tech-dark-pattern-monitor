"""Welche Signale sind Feststellungen, welche sind Ableitungen?

Diese Unterscheidung traegt C4 aus docs/ABSTIMMUNG_Regelwerk.md:

    Stuetzt sich applies_when auf eine *unbestaetigte Ableitung*,
    darf die Regel hoechstens "verdaechtig" erreichen.

Entscheidend ist das Wort "unbestaetigt". Ohne die Liste hier wuerde jede
Voraussetzung als Ableitung gelten — dann waere auch banner_detected eine,
obwohl das eine unmittelbare Beobachtung ist, und keine Regel koennte je
"eindeutig" werden.

Aufgenommen ist deshalb nur, was nach ABSTIMMUNG_Regelwerk.md Korb C eine
rechtliche Qualifikation oder eine ausdrueckliche Heuristik ist. Alles
andere gilt als Feststellung.

Aufheben laesst sich die Begrenzung je Ziel in data/targets/<name>.yaml:

    bestaetigt_durch_mensch:
      is_b2c_offer: true      # geprueft: <Kuerzel>, <Datum>

OFFEN: Sobald _SIGNALE.md eine eigene Spalte dafuer bekommt, faellt diese
Datei weg und die Herkunft wird dort gelesen. Bis dahin ist sie die eine
Stelle, an der die Unterscheidung steht — nicht verstreut im Code.
"""

ABLEITUNGEN = frozenset({
    # ausdrueckliche Heuristik laut _SIGNALE.md
    "is_b2c_offer",
    "is_consumer_offer",        # anderer Name fuer dasselbe
    "is_consumer_contract",     # dito

    # rechtliche Qualifikationen, aus Tatsachen abgeleitet (Korb C)
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


def ist_ableitung(signalname: str) -> bool:
    return signalname in ABLEITUNGEN
