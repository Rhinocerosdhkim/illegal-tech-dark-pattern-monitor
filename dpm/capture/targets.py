"""The target profile: everything that is site-specific.

Selectors, the path and the prerequisites a human signed off belong in
data/targets/<name>.yaml and never in the code. That is what makes the
capture layer maintainable by whoever is there on the day viagogo changes
its markup (ARBEITSTEILUNG_Technik.md 2.2).

A site without a profile still runs. It only starts from its URL and takes
the industry as unknown -- deliberately, because the tool is meant for any
website, not only the ones we prepared (data/fixtures/README.md).
"""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

import yaml

ROOT = Path(__file__).resolve().parents[2]
TARGETS = ROOT / "data" / "targets"

_SAFE_NAME = re.compile(r"^[\w.\-]+$")


def slug(url: str) -> str:
    """A URL or a bare name reduced to something usable as a directory name.

    It ends up in run_id and in the output path, so it may not carry a
    scheme, a slash or anything else that could leave the output folder.
    """
    rest = re.sub(r"^[a-zA-Z][\w+.\-]*://", "", url)
    host = rest.split("/")[0]
    host = re.sub(r"^www\.", "", host)
    host = re.sub(r"\.(de|com|net|org|eu|at|ch)$", "", host)
    if not host:                                # file:/// has no host
        host = PurePosixPath(rest).stem
    return re.sub(r"[^\w.\-]", "-", host).strip("-.") or "target"


def load(name_or_url: str, directory: Path | None = None) -> dict:
    """Find a profile by name or by URL. Returns {} if there is none.

    The name in the profile is what capture.json must carry as meta.target:
    the engine looks the profile up again under exactly that name, and with
    a hostname like "viagogo.de" it would silently not find "viagogo.yaml"
    -- and with it lose the prerequisites confirmed by a human.
    """
    directory = Path(directory or TARGETS)
    name = slug(name_or_url) if "://" in name_or_url else name_or_url

    if not _SAFE_NAME.match(name):
        return {}
    file = directory / f"{name}.yaml"
    if not file.exists():
        return {}

    profile = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
    return profile if isinstance(profile, dict) else {}
