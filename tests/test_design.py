"""The design promises two things that are easy to break silently.

1. The four verdict levels stay apart in greyscale. The Beweisakte is
   printed and filed; if colour is the only carrier, a photocopy loses the
   difference between "eindeutig" and "unauffaellig". The design handoff
   asks for exactly this check ("Druckprobe · Graustufen").

2. Nothing on the page is fetched from a third party. Every generated view
   states "keine Uebertragung an Dritte" in its own title bar, and a
   webfont link would make that untrue — quite apart from the document
   then rendering differently once the network is gone.
"""

import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.report.design import fonts

OUT = pathlib.Path("out")
VIEWS = ["index.html", "marktuebersicht/marktuebersicht.html"]
LEVELS = ["eindeutig", "verdaechtig", "unklar", "unauffaellig"]

print("Fonts are carried, not fetched")
css = fonts()
assert css.count("@font-face") >= 5, "fonts missing from the stylesheet"
assert "data:font/woff2;base64," in css, "fonts are linked rather than embedded"
assert "http" not in css, "the stylesheet reaches out to a network host"
print(f"  ok  {css.count('@font-face')} faces embedded, no external source")

print("\nNo view loads anything from a third party")
pages = [OUT / name for name in VIEWS]
pages += sorted(OUT.glob("*/beweisakte.html"))[:1]
pages += sorted(OUT.glob("zeitachse_*/zeitachse.html"))[:1]
for page in pages:
    if not page.exists():
        print(f"  -   {page} not built, skipped")
        continue
    html = page.read_text(encoding="utf-8")
    external = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    assert not external, f"{page.name} loads from outside: {external}"
    print(f"  ok  {page.name}")

print("\nThe four levels stay apart without colour")
try:
    from playwright.sync_api import sync_playwright
except ImportError:                                   # pragma: no cover
    print("  -   Playwright not installed, skipped")
    sys.exit(0)

sample = OUT / "marktuebersicht" / "marktuebersicht.html"
assert sample.exists(), "run 'python -m dpm rebuild' first"

with sync_playwright() as play:
    browser = play.chromium.launch()
    page = browser.new_page()
    page.goto(sample.resolve().as_uri())

    # Put one chip of every level on the page and read back what actually
    # distinguishes them. Colour is deliberately not part of the signature.
    signatures = {}
    for level in LEVELS:
        page.evaluate(
            """(level) => {
                 let probe = document.getElementById('probe');
                 if (!probe) {
                   probe = document.createElement('div');
                   probe.id = 'probe';
                   document.body.appendChild(probe);
                 }
                 probe.innerHTML = '<span class="stufe ' + level + '">x</span>';
               }""", level)
        chip = page.eval_on_selector(
            "#probe .stufe",
            """e => {
                 const s = getComputedStyle(e);
                 const m = getComputedStyle(e, '::before');
                 return [s.borderTopWidth, s.borderTopStyle,
                         m.borderRadius, m.transform,
                         m.backgroundColor === 'rgba(0, 0, 0, 0)' ? 'hollow' : 'filled'
                        ].join('|');
               }""")
        signatures[level] = chip
        print(f"  {level:14} {chip}")

    browser.close()

distinct = set(signatures.values())
assert len(distinct) == len(LEVELS), (
    "two levels are indistinguishable once colour is removed: "
    f"{signatures}")
print(f"  ok  {len(distinct)} distinct signatures for {len(LEVELS)} levels")

# The heaviest level has to carry the heaviest frame, and it has to survive
# the browser rounding border widths to whole pixels.
weight = {level: int(signatures[level].split("|")[0].rstrip("px").split(".")[0])
          for level in LEVELS}
assert weight["eindeutig"] > weight["unauffaellig"], (
    f"eindeutig does not read as heavier than unauffaellig: {weight}")
print(f"  ok  eindeutig {weight['eindeutig']}px vs "
      f"unauffaellig {weight['unauffaellig']}px")

print("\nAll design tests passed.")
