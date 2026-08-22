"""The agency asked for a "Tabelle (z. B. PDF) mit Filtermöglichkeit und
Statistiken". A PDF that always prints the unfiltered table answers only
half of that — so the export has to carry the selection somebody made, and
say in the document which selection that was.
"""

import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from playwright.sync_api import sync_playwright

from dpm.engine.rules import load_rules
from dpm.report.diff import build as build_timeline, compare
from dpm.report.overview import build as build_overview, collect
from dpm.report.pdf import apply_filters

RULES = load_rules()
FOLDERS = ["data/fixtures/viagogo", "data/fixtures/nachrichtenportal",
           "data/fixtures/sauberer-shop", "data/fixtures/ratgeber-portal"]

print("Marktübersicht")
overview = collect(FOLDERS, RULES)
with tempfile.TemporaryDirectory() as tmp:
    result = build_overview(overview, output=tmp, as_pdf=True,
                            selection={"branche": "Ticketing",
                                       "stufe": "verdaechtig"})
    assert result["pdf"] and result["pdf"].exists()
    assert result["pdf"].stat().st_size > 20_000, "PDF suspiciously small"
    print(f"  ok  PDF written, {result['pdf'].stat().st_size // 1024} kB")

    html = result["html"]
    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page()
        page.goto(html.resolve().as_uri())
        page.wait_for_timeout(150)
        before = int(page.inner_text("#sichtbar"))

        page.evaluate(apply_filters({"branche": "Ticketing",
                                     "stufe": "verdaechtig"}))
        page.wait_for_timeout(150)
        after = int(page.inner_text("#sichtbar"))
        assert 0 < after < before, f"{before} -> {after}"
        print(f"  ok  filter narrows the table: {before} -> {after} rows")

        note = page.inner_text("#filter-hinweis")
        assert "Ticketing" in note and "verdächtig" in note, note
        print(f"  ok  the document states its own filter: {note!r}")

        # An unknown value must not silently empty the table.
        page.reload(); page.wait_for_timeout(150)
        page.evaluate(apply_filters({"branche": "Gibtesnicht"}))
        page.wait_for_timeout(150)
        assert int(page.inner_text("#sichtbar")) == before
        print("  ok  an unknown filter value is ignored, not applied blindly")

        page.emulate_media(media="print"); page.wait_for_timeout(150)
        assert page.eval_on_selector(".filterleiste", "e => getComputedStyle(e).display") \
            == "none"
        assert page.eval_on_selector("#filter-hinweis",
                                     "e => getComputedStyle(e).display") != "none"
        print("  ok  in print: controls hidden, filter caption shown")
        browser.close()

print("\nZeitachse")
timeline = compare("data/fixtures/viagogo", "data/fixtures/viagogo-2026-09", RULES)
with tempfile.TemporaryDirectory() as tmp:
    result = build_timeline(timeline, output=tmp, as_pdf=True)
    assert result["pdf"] and result["pdf"].exists()
    print(f"  ok  PDF written, {result['pdf'].stat().st_size // 1024} kB")
    result = build_timeline(timeline, output=tmp, as_pdf=False)
    assert result["pdf"] is None
    print("  ok  without --pdf no PDF is produced")

print("\nAll PDF export tests passed.")
