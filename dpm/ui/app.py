"""The three views as a local web app.

This is an addition, not the delivery path. Everything it shows is a file
in `out/`, produced by `python -m dpm rebuild` and readable by opening
`out/index.html` — no server needed. That stays true on purpose: from
Tuesday nobody from the development team is available, and a server is
one more thing that can fail in somebody else's hands.

What the app adds is the half that a folder of files cannot do: starting
a capture and watching it run.
"""

from __future__ import annotations

import asyncio
import re
import secrets
from pathlib import Path

from dpm import PRODUCT_NAME
from dpm.ai.client import Model, unavailable as model_unavailable
from dpm.ai.doc_import import INDUSTRIES
from dpm.capture.targets import load as load_target, slug
from dpm.engine.discovery import find_runs
from dpm.engine.rules import load_rules
from dpm.engine.run import load_run
from dpm.engine.verdict import assess
from dpm.report.archive import relative
from dpm.report.case_file import LEVEL_CLASS_ORDER, _environment
from dpm.report.case_file import build as build_case_file
from dpm.ui.runner import DONE, FAILED, RUNNING, Lauf, Runs

MISSING = ("FastAPI und uvicorn fehlen.\n"
           "  .venv/bin/pip install -r requirements.txt\n\n"
           "Ohne sie bleibt alles nutzbar: python -m dpm rebuild erzeugt\n"
           "out/index.html, das im Browser geoeffnet wird.")


def create(output: Path = Path("out")) -> object:
    """Build the app. Imported lazily so `python -m dpm` runs without it."""
    # Imported here, not at module level: `python -m dpm` must run
    # without FastAPI installed. For the same reason no handler
    # annotates a FastAPI type -- with `from __future__ import
    # annotations` the hint is a string that FastAPI resolves in
    # the module namespace, where these names do not exist.
    from fastapi import FastAPI, Form, HTTPException
    from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
    from fastapi.staticfiles import StaticFiles

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title=f"{PRODUCT_NAME} — Prüfprogramm")
    runs = Runs()
    templates = _environment()

    def render(name: str, **context) -> HTMLResponse:
        page = templates.get_template(name).render(
            produkt=PRODUCT_NAME, stufen=LEVEL_CLASS_ORDER,
            branchen=INDUSTRIES, **context)
        return HTMLResponse(page)

    def archive() -> list:
        """Every capture on disk, with what the rulebook makes of it."""
        rules = load_rules()
        entries = []
        # The same places rebuild looks in: live runs under out/ and the
        # reference cases under data/fixtures/. The rendered Beweisakte
        # always lands in the output folder, never next to the capture.
        for path in find_runs():
            run = load_run(path)
            findings = [assess(rule, run.table) for rule in rules]
            counts = {}
            for finding in findings:
                if finding.reportable:
                    counts[finding.level] = counts.get(finding.level, 0) + 1
            folder = output / run.run_id
            entries.append({
                "target": run.target, "industry": run.industry,
                "timestamp": run.meta.get("timestamp"), "run_id": run.run_id,
                "counts": counts, "findings": sum(counts.values()),
                "html": f"/akte/{run.run_id}/beweisakte.html"
                        if (folder / "beweisakte.html").exists() else None,
                "pdf": f"/akte/{run.run_id}/beweisakte.pdf"
                       if (folder / "beweisakte.pdf").exists() else None})
        return sorted(entries, key=lambda e: e["timestamp"] or "", reverse=True)

    async def perform(lauf: Lauf) -> None:
        """Capture, then immediately turn the result into a Beweisakte.

        Doing the report here is the point: a run that stops at
        capture.json leaves the person with a file they cannot read.

        Two capture paths, and which one runs depends on one thing only:
        whether a model key is there. With a key the agent walks the
        funnel -- search, product, basket -- which is where the patterns
        the consumer agency named actually live. Without one the driver
        takes the start page and measures every DOM signal on it. The
        second is not a lesser demo, it is the one that still works when
        the free tier runs out on presentation day.
        """
        import json as _json

        if model_unavailable():
            from dpm.capture.driver import capture

            lauf.note = ("Kein Modell verfügbar — Startseite statt Trichter. "
                         "Die im DOM messbaren Signale werden trotzdem "
                         "erhoben.")
            profile = load_target(lauf.url) or {"name": lauf.target}
            if lauf.industry:
                profile = {**profile, "industry": lauf.industry}
            result = await capture(lauf.url, profile, None, output_root=output)
            result.write()
            lauf.folder, lauf.run_id = result.path, result.meta["run_id"]
            lauf.steps = [{"step": s.get("step"), "url": s.get("url"),
                           "screenshot": s.get("screenshot")}
                          for s in result.steps]
        else:
            from dpm.capture.main import walk

            folder = Path(await walk(lauf.url, lauf.industry or "unbekannt",
                                     output_root=output))
            lauf.folder = folder
            lauf.run_id = folder.name
            written = _json.loads((folder / "capture.json").read_text(
                encoding="utf-8"))
            lauf.steps = [{"step": s.get("step"), "url": s.get("url"),
                           "screenshot": s.get("screenshot")}
                          for s in written.get("steps", [])]

        # In a worker thread on purpose: the PDF is printed through the
        # synchronous Playwright API, which refuses to run inside a live
        # asyncio loop. Without the thread the Beweisakte would silently
        # arrive as HTML only.
        def report() -> None:
            # lauf.folder, not a variable from one of the two branches:
            # the agent path has no `result` and the closure raised
            # NameError there, which arrived as a failed run after the
            # capture had already succeeded.
            run = load_run(lauf.folder)
            rules = load_rules()
            build_case_file(run, [assess(rule, run.table) for rule in rules],
                            output=output, as_pdf=True)

        await asyncio.to_thread(report)

    def across_targets() -> dict:
        """The outputs that are about all targets rather than one.

        They are files in the same folder, so the page can only offer what
        `rebuild` has actually written — a link to a document that was
        never built is a claim that it exists.
        """
        def link(path: Path) -> str | None:
            return f"/akte/{path.relative_to(output)}" if path.exists() else None

        markt = output / "marktuebersicht"
        zeitachsen = []
        for folder in sorted(output.glob("zeitachse_*")):
            page = folder / "zeitachse.html"
            if page.exists():
                zeitachsen.append({
                    # zeitachse_<timestamp>_<target> -- the target is the tail
                    "ziel": folder.name.split("_", 2)[-1],
                    "html": link(page), "pdf": link(folder / "zeitachse.pdf")})
        return {
            "uebersicht": {"html": link(markt / "marktuebersicht.html"),
                           "csv": link(markt / "marktuebersicht.csv"),
                           "pdf": link(markt / "marktuebersicht.pdf")},
            "zeitachsen": zeitachsen,
        }

    @app.get("/", response_class=HTMLResponse)
    def auftrag():
        akten = archive()
        return render("auftrag.html", akten=akten,
                      laeuft=runs.busy(), letzter=runs.latest(),
                      modell=model_unavailable(), **across_targets())

    @app.post("/prueflauf")
    async def start(url: str = Form(...), branche: str = Form("")):
        url = (url or "").strip()
        if not url:
            raise HTTPException(400, "Ohne Adresse kein Prüflauf.")
        # Only a bare host gets a scheme. Prepending one unconditionally
        # turned "file:///tmp/x.html" into "https://file:///tmp/x.html",
        # which captured nothing and reported "fertig" with zero shots.
        if not re.match(r"^[a-zA-Z][\w+.\-]*://", url):
            url = "https://" + url
        if runs.busy():
            raise HTTPException(
                409, "Es läuft bereits eine Erfassung. Zwei Ziele "
                     "gleichzeitig widersprechen der vereinbarten "
                     "Abrufregel und verfälschen die Zeitmessung.")

        lauf = Lauf(token=secrets.token_urlsafe(8), target=slug(url),
                    industry=branche.strip(), url=url, output=output)
        runs.start(lauf, perform(lauf))
        return RedirectResponse(f"/prueflauf/{lauf.token}", status_code=303)

    @app.get("/prueflauf/{token}", response_class=HTMLResponse)
    def prueflauf(token: str):
        lauf = runs.get(token)
        if lauf is None:
            raise HTTPException(404, "Diesen Lauf kennt der Server nicht.")
        return render("prueflauf.html", lauf=lauf.snapshot())

    @app.get("/prueflauf/{token}/status")
    def status(token: str):
        lauf = runs.get(token)
        if lauf is None:
            raise HTTPException(404, "unbekannt")
        return JSONResponse(lauf.snapshot())

    app.mount("/akte", StaticFiles(directory=output), name="akte")
    return app


def serve(host: str = "127.0.0.1", port: int = 8000,
          output: Path = Path("out")) -> int:
    """Start the local server, or say plainly why it cannot start."""
    try:
        import uvicorn                                    # noqa: F401
        import fastapi                                    # noqa: F401
    except ImportError:
        print(f"\n{MISSING}\n")
        return 1

    import uvicorn
    print(f"\n{PRODUCT_NAME} laeuft auf http://{host}:{port}")
    print("Beenden mit Strg-C. Alles, was hier entsteht, liegt zugleich "
          f"als Datei unter {Path(output).resolve()}\n")
    uvicorn.run(create(output), host=host, port=port, log_level="warning")
    return 0
