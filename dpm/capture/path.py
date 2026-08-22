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


def depth(step: str) -> int:
    """How far along the funnel a step lies. Anything unknown ranks lowest."""
    try:
        return PATH_STEPS.index(step)
    except ValueError:
        return -1


def _says_nothing(value) -> bool:
    """Did the measurement find anything? false, 0 and "" found nothing."""
    return value is None or value is False or value == 0 or value == ""


def supersedes(new_value, new_step: str, old_value, old_step: str) -> bool:
    """May a fresh measurement replace one this capture already holds?

    Both producers -- the model reading a screenshot and extractors.js
    reading the DOM -- used to assign unconditionally, so it was the loop
    order that decided. That produced two wrong answers in opposite
    directions:

        banner_detected true on startseite, false on produktdetail. The
        banner is gone because it was accepted, and the capture ends up
        saying the shop never had one.

        has_price_display true and vat_disclosure_present false, both read
        off a checkout page, overwrite the correct pair from the product
        page -- which is exactly the DP-005 verdaechtig condition, fired
        against a page nobody looked at.

    So the rule is not simply "the deeper step wins". A later page that
    shows nothing is not a denial of what an earlier page showed:

        a measurement that found nothing never replaces one that found
        something, in either direction along the path;

        a measurement that found something always beats one that found
        nothing, however shallow it is;

        and between two findings of the same kind the deeper step wins,
        because the seminar of 19.08. put the interesting patterns on the
        product page, not on the start page.
    """
    if _says_nothing(new_value) and not _says_nothing(old_value):
        return False
    if not _says_nothing(new_value) and _says_nothing(old_value):
        return True
    return depth(new_step) >= depth(old_step)
