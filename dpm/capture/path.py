"""The path a capture walks through a site.

The consumer agency pointed out in the seminar of 19.08. that the
interesting patterns are not on the start page: "only 2 left" and the VAT
note appear once you open a product. So a capture is not one URL, it is a
path -- and every signal carries the step it was measured on.

    startseite -> suchergebnis -> produktdetail -> warenkorb -> bestelluebersicht

STILL MISSING (capture layer, Karthik): the six verbs
navigate / search / click / click_first_result / scroll / wait, driven from
data/targets/<name>.yaml. Until they exist the navigator guesses its way
through by sight, which cannot reach a product page on a site that requires
a search -- see dpm/capture/README.md.
"""

from __future__ import annotations

# Fixed vocabulary. The step name ends up in capture.json, in the evidence
# binding and in the German Beweisakte, so it must not be invented per run.
PATH_STEPS = ("startseite", "suchergebnis", "produktdetail",
              "warenkorb", "bestelluebersicht")

# Written instead of a step name when the path did not get through. It is
# not a path step and no signal may be attributed to it.
ABANDONED = "abgebrochen"

# The page we are on is not on the funnel at all: a login wall, a captcha,
# a 404, an interstitial. Distinct from ABANDONED, which says the walk
# stopped -- this one says where we are standing.
#
# It exists because the navigator had no way to say it. Its schema offered
# only the five path steps, so a login page had to be labelled with one of
# them, and everything measured there became a fact about that step: a
# capture of 22.08. recorded "no countdown, no scarcity note, no VAT
# problem" for viagogo, all of it read off an Anmeldung screen. A silent
# all-clear is the worst thing this tool can produce, so the navigator has
# to be able to say "not here", and nothing may be attributed to it.
OFF_PATH = "abseits"


# The consent banner is shown at first contact and is gone once it was
# answered. Everything measured on it therefore belongs to the step where
# we met it, and a later page that no longer shows it is not saying the
# site never had one. Exactly the signals of the "Consent-Banner und
# Bedienelemente" table in rules/_SIGNALE.md.
FIRST_CONTACT = frozenset({
    "banner_detected", "accept_button_area_px2", "reject_button_area_px2",
    "accept_contrast_ratio", "reject_contrast_ratio", "reject_button_present",
    "reject_click_depth", "preselected_checkbox_count",
    "third_party_cookies_before_consent", "banner_reappears_on_reject",
    "banner_reappears_count_24h", "more_info_present",
    "more_info_leads_to_reject", "more_info_click_depth",
})


def depth(step: str) -> int:
    """How far along the funnel a step lies. Anything unknown ranks lowest."""
    try:
        return PATH_STEPS.index(step)
    except ValueError:
        return -1


def supersedes(name: str, new_step: str, old_step: str) -> bool:
    """May a fresh measurement replace one this capture already holds?

    Both producers -- the model reading a screenshot and extractors.js
    reading the DOM -- used to assign unconditionally, so the loop order
    decided. The consent banner then vanished from the record: measured
    true on the start page, measured false on the product page because it
    had been accepted, and DP-001 fell away.

    Which measurement is authoritative is a property of the signal, not of
    its value. The first version of this function asked whether a value
    "found something", treating false as a non-finding -- but false IS the
    finding in four of the six rules: vat_disclosure_present == false is
    the § 3 PAngV violation, reject_button_present == false is the one
    condition in DP-001 that carries "eindeutig". Blocking those made real
    violations unreachable.

    So: the banner signals belong to the first contact and keep it, and
    everything else is authoritative at the deepest step it was seen at,
    because the consumer agency pointed out in the seminar of 19.08. that
    the interesting patterns are on the product page.
    """
    if name in FIRST_CONTACT:
        return False
    return depth(new_step) >= depth(old_step)
