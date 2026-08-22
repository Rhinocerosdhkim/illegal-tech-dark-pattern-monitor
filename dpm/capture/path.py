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
