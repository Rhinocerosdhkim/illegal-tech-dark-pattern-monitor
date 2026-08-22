"""Find the capture runs that are lying around, and group them by target.

This is what turns the timeline from a feature somebody has to remember
into one the tool performs. Until now a person had to name both folders by
hand — and a monitor that only notices a quietly reintroduced design when
somebody remembers to look for it is not a monitor.

The run folder name is not trusted for this. The target and the timestamp
are read out of each capture.json, because the folder can be renamed and
the file cannot lie about what it contains.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Where captures normally live: real runs in out/, the hand-written ones in
# data/fixtures/. Both, so a handover works whether or not anything has been
# captured yet.
DEFAULT_PLACES = (ROOT / "out", ROOT / "data" / "fixtures")


def find_runs(*places) -> list:
    """Every folder below `places` that holds a readable capture.json."""
    found = []
    for place in (places or DEFAULT_PLACES):
        place = Path(place)
        if not place.exists():
            continue
        for capture in sorted(place.rglob("capture.json")):
            if _meta(capture) is not None:
                found.append(capture.parent)
    return found


def by_target(paths) -> dict:
    """target -> runs, oldest first.

    Runs whose capture.json cannot be read are dropped here rather than
    later: a broken file should not take the whole rebuild down.
    """
    groups: dict = {}
    for path in paths:
        meta = _meta(Path(path) / "capture.json")
        if meta is None:
            continue
        target = meta.get("target") or meta.get("ziel")
        if not target:
            continue
        groups.setdefault(str(target), []).append(
            (str(meta.get("timestamp") or ""), Path(path), meta))

    return {target: [(p, m) for _, p, m in sorted(runs)]
            for target, runs in groups.items()}


def pairs_to_compare(groups: dict) -> list:
    """(target, earlier, later, note) for every target captured twice.

    Compared are the two MOST RECENT captures — the monitoring question is
    "what changed since we last looked". For any other pair the explicit
    `dpm timeline <a> <b>` is still there.

    A hand-written fixture is never paired with a real capture: they use
    different viewports and a different capture method, so the diff would
    look plausible and mean nothing. Same reason `compare()` warns about
    differing viewports.
    """
    result = []
    for target, runs in sorted(groups.items()):
        if len(runs) < 2:
            continue
        (earlier, earlier_meta), (later, later_meta) = runs[-2], runs[-1]
        if earlier_meta.get("capture_mode") != later_meta.get("capture_mode"):
            result.append((target, None, None,
                           f"{target}: die beiden juengsten Erfassungen sind "
                           f"unterschiedlich entstanden "
                           f"({earlier_meta.get('capture_mode')} und "
                           f"{later_meta.get('capture_mode')}). Ein Vergleich "
                           f"waere ohne Aussagekraft und unterbleibt."))
            continue
        result.append((target, earlier, later, ""))
    return result


def _meta(capture: Path):
    try:
        content = json.loads(capture.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return content.get("meta") if isinstance(content, dict) else None
