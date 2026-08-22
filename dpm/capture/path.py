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
