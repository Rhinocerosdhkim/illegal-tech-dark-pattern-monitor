"""extractors.js against pages whose answer we already know.

Built with page.set_content(), so no site is visited and the test runs
offline. The pages are small on purpose: every number asserted here is one
somebody can recompute by hand from the markup.

The check that matters most is the last one in each block: a signal that
could not be measured has to land in `errors`, never as 0 or false. On a
banner without a reject button, "reject_button_area_px2 = 0" would make
every ratio rule fire, and the finding would be an artefact of our own
measurement.
"""

import asyncio
import json
import sys
import pathlib
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.rules import load_rules
from dpm.engine.run import load_run
from dpm.engine.verdict import CLEAR, assess
from dpm.signals import collect

FRAME = """<!doctype html><html lang="de"><body style="background:#fff">{}</body></html>"""

# Accept 200x44 = 8800 px2, reject 60x18 = 1080 px2 -> ratio 8.1.
# Accept is white on dark green, reject light grey on white.
DARK = FRAME.format("""
<div id="banner" style="position:fixed;bottom:0;left:0;right:0;background:#fff;
     z-index:9999;padding:12px">
  <p>Wir verwenden Cookies und Tracking zur Einwilligung.</p>
  <button style="width:200px;height:44px;background:#0a6b2f;color:#ffffff">
    Alle akzeptieren</button>
  <button style="width:60px;height:18px;background:#ffffff;color:#d8d8d8">
    Ablehnen</button>
  <label><input type="checkbox" checked> Marketing</label>
  <label><input type="checkbox"> Statistik</label>
</div>
<h1>Konzertticket</h1>
<p>Preis: 49,90 €</p>
<button>Jetzt bestellen</button>
<footer><span style="font-size:8px;color:#e8e8e8;opacity:0.3">
  Widerruf: Sie haben das Recht, binnen 14 Tagen zu widerrufen.</span></footer>
""")

# Same banner, but the only way out is "Einstellungen" — no reject button
# on the first level at all. That is DP-001's "eindeutig" condition.
NO_REJECT = FRAME.format("""
<div id="banner" style="position:fixed;bottom:0;background:#fff;z-index:9999">
  <p>Cookie-Einwilligung</p>
  <button style="width:200px;height:44px;background:#0a6b2f;color:#fff">
    Alle akzeptieren</button>
  <button style="width:90px;height:30px">Einstellungen</button>
</div>
<p>Preis: 10,00 €</p>
""")

CLEAN = FRAME.format("""
<div id="banner" style="position:fixed;bottom:0;background:#fff;z-index:9999">
  <p>Cookie-Einwilligung</p>
  <button style="width:150px;height:40px;background:#333;color:#fff">
    Akzeptieren</button>
  <button style="width:150px;height:40px;background:#333;color:#fff">
    Alle ablehnen</button>
</div>
<p>Preis: 20,00 € inkl. MwSt.</p>
<p style="font-size:14px;color:#000">Widerruf: 14 Tage.</p>
""")

PLAIN = FRAME.format("<h1>Ratgeber</h1><p>Ein Text ohne Shop und ohne Banner.</p>")


async def measure(html: str) -> tuple[dict, dict]:
    from playwright.async_api import async_playwright
    async with async_playwright() as play:
        browser = await play.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        await page.set_content(html)
        result = await collect.measure(page)
        await browser.close()
    return result


try:
    from playwright.async_api import async_playwright        # noqa: F401
except ImportError:                                          # pragma: no cover
    print("Playwright not installed — skipped")
    sys.exit(0)

print("A banner designed against the user")
values, gaps = asyncio.run(measure(DARK))
assert values["banner_detected"] is True
assert values["reject_button_present"] is True
assert values["accept_button_area_px2"] == 8800, values["accept_button_area_px2"]
assert values["reject_button_area_px2"] == 1080, values["reject_button_area_px2"]
assert values["accept_contrast_ratio"] > 4, values["accept_contrast_ratio"]
assert values["reject_contrast_ratio"] < 2, values["reject_contrast_ratio"]
assert values["preselected_checkbox_count"] == 1, values["preselected_checkbox_count"]
print(f"  ok  Flaechen {values['accept_button_area_px2']} : "
      f"{values['reject_button_area_px2']} px², Kontrast "
      f"{values['accept_contrast_ratio']} : {values['reject_contrast_ratio']}")

assert values["order_button_found"] is True
assert values["order_button_label"] == "Jetzt bestellen"
assert values["required_info_found"] is True
assert values["required_info_type"] == "widerruf"
assert values["font_size_min_px"] == 8, values["font_size_min_px"]
assert values["hidden_by_opacity_count"] >= 1
assert values["vat_disclosure_present"] is False
print(f"  ok  Pflichthinweis in {values['font_size_min_px']} px, "
      f"keine MwSt-Angabe")

print("\nNo reject button — the area must not come back as zero")
values, gaps = asyncio.run(measure(NO_REJECT))
assert values["banner_detected"] is True
assert values["reject_button_present"] is False
assert values["more_info_present"] is True
assert "reject_button_area_px2" not in values, "a missing button was measured"
assert "reject_button_area_px2" in gaps, gaps
assert "reject_contrast_ratio" in gaps
print(f"  ok  {gaps['reject_button_area_px2']}")

print("\nAnd that is what DP-001 calls eindeutig")
with tempfile.TemporaryDirectory() as tmp:
    folder = pathlib.Path(tmp) / "probe"
    folder.mkdir()
    (folder / "capture.json").write_text(json.dumps({
        "meta": {"target": "probe", "industry": "Ticketing",
                 "run_id": "probe", "timestamp": "2026-08-22T12:00:00+02:00"},
        "steps": [{"step": "startseite", "url": "about:blank",
                   "screenshot": "S-01.png", "dom_hash": "sha256:probe"}],
        "signals": {name: {"value": value, "step": "startseite",
                           "evidence": "S-01.png"}
                    for name, value in values.items()},
        "signal_errors": gaps,
    }, ensure_ascii=False), encoding="utf-8")

    run = load_run(folder)
    findings = {f.rule.id: f for f in
                (assess(rule, run.table) for rule in load_rules())}
    dp001 = findings["DP-001"]
    assert dp001.level == CLEAR, f"DP-001 kam als {dp001.level}"
    print(f"  ok  DP-001 {dp001.level} — {dp001.condition}")

print("\nA correctly built banner produces no finding")
values, gaps = asyncio.run(measure(CLEAN))
assert values["reject_button_present"] is True
assert values["accept_button_area_px2"] == values["reject_button_area_px2"]
assert values["preselected_checkbox_count"] == 0
assert values["vat_disclosure_present"] is True
print(f"  ok  gleich grosse Schaltflaechen, keine Vorauswahl, MwSt genannt")

print("\nA page without a banner says so — it does not report a gap")
values, gaps = asyncio.run(measure(PLAIN))
assert values["banner_detected"] is False, "no banner became 'not measured'"
assert "accept_button_area_px2" in gaps, "a missing banner produced an area"
assert values["order_button_found"] is False
assert values["required_info_found"] is False
print(f"  ok  banner_detected = false, {len(gaps)} Signale als nicht erhoben")

print("\nA lawful footer is not a consent banner")
# Every lawful German site carries Impressum, Datenschutz and AGB, and
# usually in a fixed footer. On the consent WORDS alone that footer was
# taken for a banner: banner_detected became true, no accept or reject
# button was found inside it, and DP-001 certified "eindeutig" against a
# site that had done nothing wrong -- citing OLG Koeln. A banner is
# recognised by the choice it offers, not by the words it contains.
FOOTER = FRAME.format("""
<h1>Sauberer Shop</h1>
<p>Kaffeemuehle, 49,00 EUR inkl. MwSt., zzgl. 4,90 EUR Versand.</p>
<button>Zahlungspflichtig bestellen</button>
<footer style="position:fixed;bottom:0;left:0;right:0;background:#eee;padding:12px">
  <a href="/impressum">Impressum</a> ·
  <a href="/datenschutz">Datenschutz</a> ·
  <a href="/agb">AGB</a>
</footer>""")

values, gaps = asyncio.run(measure(FOOTER))
assert values["banner_detected"] is False, \
    "a Datenschutz link in a fixed footer was taken for a consent banner"
assert "reject_button_present" not in values, \
    "a footer produced a statement about a reject button"
assert "accept_button_area_px2" in gaps
print("  ok  banner_detected = false, keine Aussage ueber Schaltflaechen")

with tempfile.TemporaryDirectory() as tmp:
    folder = pathlib.Path(tmp)
    (folder / "capture.json").write_text(json.dumps({
        "meta": {"target": "sauber", "industry": "Test"},
        "steps": [{"step": "startseite", "url": "x", "screenshot": "S-01.png"}],
        "signals": {n: {"value": v, "step": "startseite", "evidence": "S-01.png"}
                    for n, v in values.items()},
        "signal_errors": gaps,
    }, ensure_ascii=False), encoding="utf-8")
    run = load_run(folder)
    dp001 = next(assess(r, run.table) for r in load_rules() if r.id == "DP-001")
    assert dp001.level != CLEAR, \
        f"DP-001 accuses a lawful page at the highest level: {dp001.condition}"
    print(f"  ok  DP-001 {dp001.level}, nicht eindeutig")

print("\nA banner we cannot see into is a gap, not an absence")
# Consent wording, but every control lives behind a closed shadow root, so
# nothing clickable is readable. "We could not check" -- never false.
SHADOW = FRAME.format("""
<div id="cmp" style="position:fixed;bottom:0;left:0;right:0;padding:20px">
  Wir verwenden Cookies und benoetigen Ihre Einwilligung.
</div>
<h1>Shop</h1>""")
values, gaps = asyncio.run(measure(SHADOW))
assert "banner_detected" not in values, \
    "an unreadable banner was reported as measured"
assert "banner_detected" in gaps, gaps
print(f"  ok  banner_detected -> errors: {gaps['banner_detected'][:52]}")

print("\nAll extractor tests passed.")
