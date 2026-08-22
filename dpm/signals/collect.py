"""Run `extractors.js` in the open page and stamp what it returns.

Thin on purpose. The measuring happens in the browser, in a file with no
Python in it, so the same code could run as a Chrome extension content
script. Everything this module does is inject it and attach the
provenance every signal has to carry.

Wiring it into a capture is one line:

    from dpm.signals import collect
    await collect.into(run, page, step=entry["step"], evidence=name)

Call it AFTER the signals read off the screenshot. A value measured in
the DOM is deterministic and reproducible by hand in the developer
tools; one read out of an image is not, so where both produce the same
signal, the measured one should be the one that survives.
"""

from __future__ import annotations

from pathlib import Path

from dpm.capture.path import supersedes

SOURCE = Path(__file__).parent / "extractors.js"


def script() -> str:
    return SOURCE.read_text(encoding="utf-8")


async def blocked(page) -> str | None:
    """Why this page is not the site, or None if it is.

    A bot check, a login wall, an error page. The navigator can say
    "abseits", but only where there is a model; without one -- the keyless
    mode, which is what the demonstration runs in -- nobody is there to
    ask. The same judgement is made in extractors.js, deterministically.
    """
    answer = await _evaluate(page)
    return answer.get("blocked") if isinstance(answer, dict) else None


async def _evaluate(page):
    try:
        return await page.evaluate(script())
    except Exception:                             # navigation, CSP, syntax
        return None


async def measure(page) -> tuple[dict, dict]:
    """(values, gaps) for the page as it currently stands.

    A failure here is not "nothing is there": it is "we could not look".
    The caller gets an empty result and a reason, and every signal the
    file would have produced stays uncaptured.
    """
    try:
        answer = await page.evaluate(script())
    except Exception as error:                    # navigation, CSP, syntax
        return {}, {"__extractors__": f"Messung im Browser fehlgeschlagen "
                                      f"({type(error).__name__}: {error})"}

    if not isinstance(answer, dict):
        return {}, {"__extractors__": "extractors.js lieferte kein Ergebnis"}
    values = answer.get("signals")
    gaps = answer.get("errors")
    return (values if isinstance(values, dict) else {},
            gaps if isinstance(gaps, dict) else {})


async def into(run, page, step: str, evidence: str) -> None:
    """Measure and write into a capture, with step and evidence attached.

    `run` is the capture object: anything with `.signals`, `.errors` and
    `.notes`. Kept duck-typed so this module does not import the driver
    it is called from.
    """
    values, gaps = await measure(page)

    for name, value in values.items():
        held = run.signals.get(name)
        if held and not supersedes(name, step, held["step"]):
            # The banner on the start page is gone once it was accepted;
            # measuring "no banner" on the product page is not a denial of
            # it. See path.supersedes for the whole rule.
            continue
        run.signals[name] = {"value": value, "step": step,
                             "evidence": evidence}
        run.errors.pop(name, None)

    for name, reason in gaps.items():
        if name == "__extractors__":
            run.notes.append(f"{step}: {reason}")
            continue
        # Never overwrite a value that was measured: a gap says "not
        # checked here", and somewhere else it may well have been.
        if name not in run.signals:
            run.errors[name] = f"{reason} (Schritt {step})"
