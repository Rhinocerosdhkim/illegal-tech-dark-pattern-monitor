"""The archive page — out/index.html.

Why this exists: from Tuesday nobody from the development team is
available, and the person who has to show the tool opens a folder. Without
this page that folder is seven directories named after run ids, and finding
the right file is guesswork.

It is deliberately a generated static file and not a served view. A server
is one more thing that can fail in somebody else's hands on the day it
matters, and the Sunday plan calls for a version that can simply be put
online — which a folder of HTML files already is.
"""

from __future__ import annotations

from pathlib import Path

from dpm import PRODUCT_NAME
from dpm.report.case_file import LEVEL_CLASS_ORDER, _environment


def relative(target: Path | None, folder: Path) -> str | None:
    """Path as written into the page, or None if there is nothing to link.

    A link that points nowhere claims an output that does not exist.
    """
    if target is None:
        return None
    target = Path(target)
    if not target.exists():
        return None
    try:
        return str(target.resolve().relative_to(folder.resolve()))
    except ValueError:
        return None


def build(entries: list, overview: dict | None = None,
          timelines: list | None = None, output: str | Path = "out") -> Path:
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=True)

    html = _environment().get_template("index.html").render(
        produkt=PRODUCT_NAME,
        akten=sorted(entries, key=lambda e: (e["target"] or "",
                                             e["timestamp"] or ""),),
        uebersicht=overview or {},
        zeitachsen=timelines or [],
        stufen=LEVEL_CLASS_ORDER,
    )
    path = folder / "index.html"
    path.write_text(html, encoding="utf-8")
    return path
