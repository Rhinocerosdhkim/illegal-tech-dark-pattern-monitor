"""The design system, in one place: fonts and verdict levels.

The three views share one stylesheet (`templates/_design.css`). Only the
pieces that need Python live here — embedding the fonts, and the mapping
from a verdict level to its chip class.

Fonts are embedded as base64 rather than linked, so a generated .html
carries everything it needs. Two reasons that matter here: the PDF is
printed by a headless browser that must not wait on a network, and the
Beweisakte may be opened from an archive long after this repository is
gone.
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

FONTS = Path(__file__).parent / "assets" / "fonts"

# family, weight, file
_FACES = [
    ("IBM Plex Sans", 400, "sans-var.woff2"),
    ("IBM Plex Sans", 500, "sans-var.woff2"),
    ("IBM Plex Sans", 600, "sans-var.woff2"),
    ("IBM Plex Mono", 400, "mono-400.woff2"),
    ("IBM Plex Mono", 500, "mono-500.woff2"),
    ("IBM Plex Serif", 400, "serif-400.woff2"),
    ("IBM Plex Serif", 600, "serif-600.woff2"),
]

# The rulebook and the engine spell the levels without umlauts; the CSS
# classes follow that spelling so the template can pass the code straight
# through.
LEVEL_CLASS = {"eindeutig": "eindeutig", "verdaechtig": "verdaechtig",
               "unklar": "unklar", "unauffaellig": "unauffaellig",
               "nicht_anwendbar": "unauffaellig"}


@lru_cache(maxsize=1)
def fonts() -> str:
    """@font-face rules with the woff2 files inlined.

    A missing font file is not worth failing the report over — the
    stylesheet names fallbacks for all three families.
    """
    rules = []
    for family, weight, filename in _FACES:
        path = FONTS / filename
        if not path.exists():
            continue
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        rules.append(
            f"@font-face{{font-family:'{family}';font-style:normal;"
            f"font-weight:{weight};font-display:block;"
            f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "\n".join(rules)
