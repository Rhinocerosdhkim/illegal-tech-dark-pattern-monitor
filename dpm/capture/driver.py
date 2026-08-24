"""Walk a target and write the Evidence Dossier.

Produces exactly the capture.json the evaluation layer reads
(data/fixtures/README.md). Everything from there on knows only that file.

Three things this layer is not allowed to get wrong:

    A measurement that failed is never null, 0, false or -1. "false" means
    measured and absent; signal_errors means we could not check. Those are
    two different legal statements and the engine turns the second into
    "unklar" on its own -- but only while they stay apart.

    A step that fails does not lose the steps before it. A partial capture
    is still evidence, and it is exactly how "unklar" should arise
    (ARBEITSTEILUNG_Technik.md 2.6). Nothing in here may raise past
    capture(): the file is always written.

    The evidence screenshot shows what a consumer sees. The numbered boxes
    the navigator needs are drawn afterwards, into a second image that is
    kept next to the run for auditing but never cited as evidence.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dpm.ai import navigator, text_signals
from dpm.ai.client import Model, ModelError
from dpm.capture.path import (ABANDONED, OFF_PATH, PATH_STEPS,
                              supersedes)
from dpm.signals import collect
from dpm.capture.targets import slug

# Fixed in code, not left to defaults. Pixel areas are meaningless without a
# fixed viewport and reproducibility is our whole claim against the ML
# approach. Locale de-DE because the keyword signals are German: an English
# page shows no "inkl. MwSt." and no "nur noch 2 verfuegbar".
VIEWPORT = {"width": 1440, "height": 900}
LOCALE = "de-DE"
TIMEZONE = "Europe/Berlin"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
              "Safari/537.36")

MAX_STEPS = 6
_OVERLAY_JS = (Path(__file__).parent / "som_overlay.js").read_text(encoding="utf-8")


@dataclass
class Capture:
    meta: dict
    path: Path
    steps: list = field(default_factory=list)
    signals: dict = field(default_factory=dict)
    errors: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        # "notes" is not part of the schema the engine reads. It is in the
        # file so that "why did this stop at step 2" survives the terminal
        # scrolling away.
        return {"meta": self.meta, "notes": self.notes, "steps": self.steps,
                "signals": self.signals, "signal_errors": self.errors}

    def write(self) -> Path:
        """capture.json next to its screenshots, one folder per run.

        The engine resolves every evidence file relative to this folder, so
        the two must not be separated -- and a second run of the same target
        must not overwrite the first, or the Zeitachse has nothing to
        compare.
        """
        file = self.path / "capture.json"
        file.write_text(json.dumps(self.as_dict(), ensure_ascii=False,
                                   indent=2), encoding="utf-8")
        return file


def _normalise(html: str) -> str:
    """Strip what changes on every request before hashing.

    Without this, nonces, ad ids and inline CSRF tokens make every capture
    of an unchanged page hash differently, and the Zeitachse diff can no
    longer tell "the page changed" from "we loaded it again". Heuristic, and
    deliberately conservative: only script and style bodies, comments and
    nonce attributes go. The visible markup -- what the hash is supposed to
    prove -- stays.
    """
    html = re.sub(r"<script\b[^>]*>.*?</script>", "<script/>", html,
                  flags=re.S | re.I)
    html = re.sub(r"<style\b[^>]*>.*?</style>", "<style/>", html,
                  flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    html = re.sub(r'\s(nonce|integrity)="[^"]*"', "", html, flags=re.I)
    return re.sub(r"\s+", " ", html).strip()


async def _human_click(page, x: float, y: float) -> None:
    """Move and click the way a person would. Viewport coordinates."""
    x += random.randint(-4, 4)
    y += random.randint(-4, 4)
    await page.mouse.move(x, y, steps=random.randint(5, 15))
    await page.wait_for_timeout(random.randint(200, 600))
    await page.mouse.click(x, y)
    await page.wait_for_timeout(random.randint(1200, 2500))


async def _settle(page) -> None:
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass                      # a page that never idles is still readable
    await page.wait_for_timeout(1200)


async def _open(playwright, stealth):
    browser = await playwright.chromium.launch(
        headless=True, args=["--disable-blink-features=AutomationControlled"])
    context = await browser.new_context(
        viewport=VIEWPORT, user_agent=USER_AGENT,
        locale=LOCALE, timezone_id=TIMEZONE)
    page = await context.new_page()
    if stealth is not None:
        await stealth.apply_stealth_async(page)
    return browser, page


async def capture(url: str, profile: dict, model: Model | None,
                  output_root: Path, max_steps: int = MAX_STEPS) -> Capture:
    """Walk the site and collect what we can. Never raises."""
    from playwright.async_api import async_playwright
    try:
        from playwright_stealth import Stealth
        stealth = Stealth()
    except ImportError:
        stealth = None

    # Stamped in the timezone the capture declares, not the machine's --
    # the same run must be reproducible from another country.
    now = datetime.now(ZoneInfo(TIMEZONE)).replace(microsecond=0)
    # Never the raw URL: it becomes the run_id and a directory name.
    target = profile.get("name") or slug(url)
    run_id = f"{now.strftime('%Y-%m-%dT%H-%M-%S')}_{target}"
    output = Path(output_root) / run_id
    run = Capture(path=output, meta={
        "target": target,
        "industry": profile.get("industry") or "unbekannt",
        "start_url": url,
        "timestamp": now.isoformat(),
        "capture_mode": "headless",
        "viewport": dict(VIEWPORT),
        "locale": LOCALE,
        "timezone": TIMEZONE,
        "user_agent": USER_AGENT,
        "run_id": run_id,
    })

    if stealth is None:
        run.notes.append("playwright-stealth is missing — bot detection is "
                         "more likely to notice us")
    if model is None:
        run.notes.append("no model available — navigation and the signals "
                         "read from the screenshots were skipped")

    output.mkdir(parents=True, exist_ok=True)
    (output / "nav").mkdir(exist_ok=True)

    async with async_playwright() as playwright:
        browser = page = None
        try:
            browser, page = await _open(playwright, stealth)
            answer = await page.goto(url, wait_until="domcontentloaded",
                                     timeout=30000)
            status = getattr(answer, "status", None)
            if status and status >= 400:
                # Not a measurement gap of the shop: we never reached it.
                # No walk, and no signal -- an error page has a DOM too, and
                # measuring it would file the error page under "startseite".
                run.notes.append(f"the start URL answered {status} — "
                                 f"nothing about this site was measured")
            else:
                await _settle(page)
                await _walk(page, run, model, output, max_steps)
        except Exception as error:
            run.notes.append(f"capture stopped: {type(error).__name__}: {error}")
        finally:
            if browser is not None:
                try:
                    await browser.close()
                except Exception:
                    pass

    if not run.steps:
        run.notes.append("no step was captured — the run has no evidence")
    _explain_gaps(run)
    return run


async def _walk(page, run: Capture, model, output: Path, max_steps: int) -> None:
    """One step per iteration: evidence, then navigation."""
    for number in range(1, max_steps + 1):
        name = f"S-{number:02d}.png"
        # The first iteration is the start page by construction -- capture()
        # navigated there. Every later step only gets its name once the
        # navigator has spoken, and until then no signal may be attributed
        # to it (see path.py on ABANDONED).
        step = PATH_STEPS[0] if number == 1 else ABANDONED

        # Evidence first, while the page is untouched by us.
        await page.screenshot(path=str(output / name))
        html = await page.content()
        entry = {"step": step, "url": page.url, "screenshot": name,
                 "dom_hash": "sha256:" + hashlib.sha256(
                     _normalise(html).encode("utf-8")).hexdigest()}
        run.steps.append(entry)

        if model is None:
            # Without a model there is no navigation, so the capture ends
            # here. The DOM signals need no model at all, and on the start
            # page the step is known -- so they are still measured and the
            # rules that rest on them still produce a finding.
            #
            # Unless what the start URL returned is not the site: a bot
            # check, a login wall, an error page. There is no navigator to
            # say "abseits" in this mode, and it is the mode anybody
            # without an API key gets, so the judgement is made from the
            # DOM instead. Measuring an interstitial and filing it under
            # "startseite" is the same silent all-clear the navigator's
            # escape hatch exists to prevent.
            wall = await collect.blocked(page)
            if wall:
                entry["step"] = OFF_PATH
                entry["blocked"] = wall
                run.notes.append(f"step {number}: {wall} — "
                                 f"nothing measured here")
                return
            await collect.into(run, page, step=step, evidence=name)
            return

        # Then the overlay, into a second image the report never cites.
        try:
            elements = await page.evaluate(_OVERLAY_JS)
            await page.screenshot(path=str(output / "nav" / name))
        except Exception as error:
            run.notes.append(f"step {number}: overlay failed ({error})")
            return
        finally:
            try:
                await page.evaluate(
                    "() => document.getElementById('dpm-som-layer')?.remove()")
            except Exception:
                pass

        try:
            decision = await navigator.decide(
                model, (output / "nav" / name).read_bytes(), PATH_STEPS,
                off_path=OFF_PATH)
        except ModelError as error:
            run.notes.append(f"step {number}: navigator failed ({error})")
            return

        entry["step"] = step = decision.step
        entry["chosen_by"] = decision.reason      # 2.9: auditable by a human

        # The model may be wrong about where it stands, and a bot check
        # looks like an ordinary page to it. A deterministic verdict from
        # the DOM overrides it, in the one direction that is safe: it can
        # withhold an attribution, never add one.
        wall = await collect.blocked(page)
        if wall:
            entry["step"] = step = OFF_PATH
            entry["blocked"] = wall

        if step == OFF_PATH:
            # A login wall, a captcha, an error page. Whatever stands here
            # says nothing about the shop, so nothing is attributed to it --
            # not as a value and not as a gap either: a later step may still
            # reach the intended page and measure it properly. The step
            # itself stays in the record, so the detour is visible in the
            # Beweisakte.
            run.notes.append(f"step {number}: not on the path "
                             f"({wall or decision.reason}) — "
                             f"nothing measured here")
        else:
            await _read_signals(run, model, output / name, step)
            # After the signals read off the screenshot, so that where both
            # produce the same signal the measured value is the one that
            # survives: it is deterministic and anybody can recompute it in
            # the developer tools.
            await collect.into(run, page, step=step, evidence=name)

        if decision.goal_reached:
            return
        if decision.target_id is None:
            run.notes.append(f"step {number} ({step}): the navigator saw no "
                             f"way further from here")
            return

        spot = elements.get(str(decision.target_id))
        if spot is None:
            run.notes.append(f"step {number} ({step}): the navigator chose box "
                             f"{decision.target_id}, which does not exist")
            return

        entry["clicked"] = spot.get("label") or f"box {decision.target_id}"
        await _human_click(page, spot["x"], spot["y"])
        await _settle(page)


async def _read_signals(run: Capture, model, screenshot: Path, step: str) -> None:
    """Read this step's screenshot and stamp the provenance on in code.

    A signal measured further down the funnel wins: the consumer agency
    pointed out that scarcity notes and the VAT line appear on the product
    page, not on the start page.
    """
    try:
        values, errors = await text_signals.read(model, screenshot.read_bytes())
    except ModelError as error:
        run.notes.append(f"{step}: reading the signals failed ({error})")
        return

    for name, value in values.items():
        held = run.signals.get(name)
        if held and not supersedes(name, step, held["step"]):
            continue
        run.signals[name] = {"value": value, "step": step,
                             "evidence": screenshot.name}
        run.errors.pop(name, None)
    for name, reason in errors.items():
        if name not in run.signals:
            run.errors[name] = f"{reason} (step {step})"


# Signals nothing in the capture layer can produce yet, with the reason
# that is true regardless of which page the walk happened to end on. A
# model looking at a broken page writes "Page is blank" into
# signal_errors, and that sentence then explains in the Beweisakte why
# § 25 TDDDG could not be checked. The structural reason has to win.
STRUCTURAL_GAPS = {
    "reject_click_depth":
        "erfordert das Ablaufen des Ablehnwegs — ein Vorgang, keine "
        "Messung; noch nicht umgesetzt",
    "banner_reappears_on_reject":
        "erfordert das Ablaufen des Ablehnwegs — ein Vorgang, keine "
        "Messung; noch nicht umgesetzt",
    "banner_reappears_count_24h":
        "erfordert Erfassungen ueber 24 Stunden; noch nicht umgesetzt",
    "more_info_leads_to_reject":
        "erfordert das Oeffnen von „Mehr Informationen“ — ein Vorgang, "
        "keine Messung; noch nicht umgesetzt",
    "third_party_cookies_before_consent":
        "steht nicht im DOM — erfordert das Auslesen des Cookie-Speichers "
        "vor jeder Interaktion; noch nicht umgesetzt",
    "countdown_unchanged_scans":
        "erfordert eine zweite Erfassung desselben Ziels; noch nicht "
        "umgesetzt",
    "scarcity_value_unchanged_scans":
        "erfordert eine zweite Erfassung desselben Ziels; noch nicht "
        "umgesetzt",
}


def _explain_gaps(run: Capture) -> None:
    """Say plainly what this capture does not measure.

    Silence would read as "measured and unremarkable". These are the signals
    the rulebook asks for and the capture layer cannot produce yet; without
    the note they would just be missing and nobody would know why.
    """
    for name in list(run.errors):
        if name in run.signals:
            # Measured after the gap was noted. Both at once would say
            # "we have a value and we could not get one".
            run.errors.pop(name)

    reached = {s["step"] for s in run.steps}
    if "produktdetail" not in reached:
        run.errors.setdefault(
            "price_listed",
            "the product page was not reached — no path execution yet")

    # What dpm/signals/extractors.js measures is not listed here any more:
    # it either has a value or has said itself why it has none. Only what
    # nothing in the capture layer produces yet stays.
    for name, reason in STRUCTURAL_GAPS.items():
        if name not in run.signals:
            run.errors[name] = reason
    for name in ("countdown_resets_on_revisit", "countdown_initial_value_sec",
                 "scarcity_value_unchanged_scans"):
        run.errors.setdefault(
            name, "requires a second capture of the same target — "
                  "not implemented yet")
