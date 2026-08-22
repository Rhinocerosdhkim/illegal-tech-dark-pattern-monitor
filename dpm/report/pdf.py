"""Print a locally generated HTML file to PDF.

Playwright is already a dependency because the capture layer needs a
browser, so we use it here instead of pulling in a second HTML-to-PDF
engine. Nothing here ever visits a website: the only URL passed to the
browser is a file:// URI pointing at a document we just wrote ourselves.

The `before` hook exists for the market overview. Its filters run in the
browser, so printing "Ticketing, only eindeutig" means: open the page,
set the filters, let the page react, then print. Without that the PDF
would always show the unfiltered table — and the agency asked for a
"Tabelle mit Filtermöglichkeit", not for one fixed table.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

A4 = {"format": "A4", "print_background": True,
      "margin": {"top": "16mm", "bottom": "16mm", "left": "14mm", "right": "14mm"}}


def footer(left: str) -> str:
    """A running footer for the printed page.

    The Beweisakte is filed on paper. A page that gets separated from the
    file has to say which procedure it belongs to and whether it is
    complete — hence the page count on every sheet.
    """
    return (
        '<div style="width:100%;margin:0 12mm;font:9px \'IBM Plex Mono\','
        'monospace;color:#8a8884;display:flex;justify-content:space-between">'
        f'<span>{escape(left)}</span>'
        '<span>Seite <span class="pageNumber"></span> von '
        '<span class="totalPages"></span></span></div>')


def render(html: Path, target: Path | None = None, before: str | None = None,
           landscape: bool = False, running_footer: str | None = None) -> Path | None:
    """Write `html` to PDF. Returns None if Playwright is not installed.

    A missing browser is not a failure: the HTML is already on disk and
    readable. From Tuesday nobody from the dev team is available, so the
    difference between "no PDF" and "no output at all" matters.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    html = Path(html)
    target = Path(target) if target else html.with_suffix(".pdf")

    with sync_playwright() as play:
        browser = play.chromium.launch()
        page = browser.new_page()
        page.goto(html.resolve().as_uri())
        if before:
            page.evaluate(before)
            page.wait_for_timeout(120)      # let the page finish reacting
        options = dict(A4)
        if running_footer:
            options |= {"display_header_footer": True,
                        "header_template": "<div></div>",
                        "footer_template": running_footer}
        page.pdf(path=str(target), landscape=landscape, **options)
        browser.close()
    return target


def apply_filters(selection: dict) -> str:
    """JS that sets the overview's filter dropdowns before printing.

    Also writes the chosen filter into the page, so the printed table says
    what it is showing. A filtered table without that line is a document
    nobody can check.
    """
    pairs = {f"f-{key}": value for key, value in selection.items() if value}
    if not pairs:
        return ""
    import json
    return f"""
    (() => {{
      const wanted = {json.dumps(pairs, ensure_ascii=False)};
      const shown = [];
      for (const [id, value] of Object.entries(wanted)) {{
        const field = document.getElementById(id);
        if (!field) continue;
        const match = Array.from(field.options).find(
          o => o.value === value || o.text === value);
        if (!match) continue;
        field.value = match.value;
        field.dispatchEvent(new Event('change'));
        shown.push(field.previousElementSibling
          ? field.previousElementSibling.textContent.trim() + ': ' + match.text
          : match.text);
      }}
      const note = document.getElementById('filter-hinweis');
      if (note && shown.length) note.textContent = shown.join('  ·  ');
    }})()
    """
