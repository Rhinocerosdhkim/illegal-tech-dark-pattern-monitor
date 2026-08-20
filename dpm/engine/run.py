"""Read one capture run.

This is the entrance to the evaluation layer. Everything from here on
knows only capture.json and the target profile — never a browser. That is
what lets the whole evaluation be built and tested against a hand-written
fixture without waiting for the capture layer.

SCHEMA. capture.json and data/targets/*.yaml use English keys. The earlier
German spellings (schritte/wert/nachweis/ziel/branche/pfad/…) are still
accepted so nothing breaks mid-migration, but they produce a warning.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .conditions import SignalTable

ROOT = Path(__file__).resolve().parents[2]
_SAFE_NAME = re.compile(r"^[\w.\-]+$")

# English key -> also accepted (legacy German spelling).
_LEGACY = {"steps": "schritte", "value": "wert", "step": "schritt",
           "evidence": "nachweis", "target": "ziel", "industry": "branche",
           "path": "pfad", "action": "aktion", "selector": "selektor",
           "confirmed_by_human": "bestaetigt_durch_mensch"}


@dataclass
class Run:
    path: Path
    meta: dict
    steps: list
    table: SignalTable
    target_profile: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)

    @property
    def run_id(self) -> str:
        raw = str(self.meta.get("run_id") or self.path.name)
        # The value comes from capture.json and becomes a directory name.
        # It must not be able to leave the output directory.
        if _SAFE_NAME.match(raw):
            return raw
        return re.sub(r"[^\w.\-]", "_", raw).lstrip(".") or "run"

    @property
    def target(self) -> str | None:
        return _field(self.meta, "target")

    @property
    def industry(self) -> str:
        return (_field(self.meta, "industry")
                or _field(self.target_profile, "industry") or "—")

    def screenshot(self, filename) -> Path | None:
        if not isinstance(filename, str) or not filename:
            return None
        path = self.path / filename
        return path if path.exists() else None


def _field(mapping: dict, name: str, default=None):
    """Read an English key, falling back to the legacy German spelling."""
    if not isinstance(mapping, dict):
        return default
    if mapping.get(name) is not None:
        return mapping[name]
    return mapping.get(_LEGACY.get(name, name), default)


def load_run(path: str | Path, targets_dir: str | Path | None = None) -> Run:
    path = Path(path)
    file = path / "capture.json" if path.is_dir() else path
    raw = json.loads(file.read_text(encoding="utf-8"))

    warnings: list = []
    meta = raw.get("meta") or {}
    errors = {k: str(v) for k, v in (raw.get("signal_errors") or {}).items()}
    values = _signals(raw.get("signals"), errors, warnings)
    steps = _steps(_field(raw, "steps") or [], warnings)

    profile = _load_target_profile(_field(meta, "target"),
                                   targets_dir or ROOT / "data" / "targets",
                                   warnings)

    # Prerequisites confirmed by a human (C4). They are value and finding at
    # once, and carry as their evidence the file somebody signed them off in.
    confirmed = set()
    for name, value in (_field(profile, "confirmed_by_human") or {}).items():
        values[name] = {"value": value, "step": "Zielprofil",
                        "evidence": f"{_field(meta, 'target')}.yaml"}
        errors.pop(name, None)
        confirmed.add(name)

    if any(_LEGACY[k] in raw or _LEGACY[k] in meta
           for k in ("steps", "target", "industry") if k in _LEGACY):
        warnings.append(
            "capture.json uses the old German key names. They are still "
            "accepted, but the agreed schema is English "
            "(steps / value / step / evidence / target / industry).")

    return Run(path=file.parent, meta=meta, steps=steps, target_profile=profile,
               warnings=warnings,
               table=SignalTable(values=values, errors=errors, confirmed=confirmed))


def _signals(raw, errors: dict, warnings: list) -> dict:
    """Read signals and enforce the shape of the contract.

    Expected per signal: {"value", "step", "evidence"}. A bare value is not
    permitted (AGENDA_Technik.md 2.1) — it cannot later be bound to a piece
    of evidence. We do not abort over it, though: from Tuesday no developer
    is available. The value is taken, the missing provenance recorded, and
    the problem reported loudly.

    "null" moves to signal_errors. null does not mean "measured and empty",
    it means "not measured" — legally a completely different statement.
    """
    values = {}
    for name, entry in (raw or {}).items():
        value = entry.get("value", entry.get("wert")) \
            if isinstance(entry, dict) else entry

        if value is None:
            errors.setdefault(name, "Wert war null — als nicht erhoben gewertet")
            warnings.append(f"Signal '{name}' had the value null and counts "
                            f"as not captured.")
            continue

        if isinstance(entry, dict):
            values[name] = {"value": value,
                            "step": _field(entry, "step"),
                            "evidence": _field(entry, "evidence")}
            continue

        warnings.append(
            f"Signal '{name}' arrived without provenance (expected: "
            f"{{value, step, evidence}}). The finding cannot be bound to a "
            f"screenshot.")
        values[name] = {"value": value, "step": None, "evidence": None}
    return values


def _steps(raw, warnings: list) -> list:
    steps = []
    for entry in raw or []:
        name = _field(entry, "step") if isinstance(entry, dict) else None
        if name:
            steps.append({**entry, "step": name})
        else:
            warnings.append(f"step without a name skipped: {entry!r}")
    return steps


def _load_target_profile(name, directory, warnings: list) -> dict:
    if not name:
        return {}
    if not _SAFE_NAME.match(str(name)):
        warnings.append(f"target name {name!r} is not a plain file name — "
                        f"no target profile loaded.")
        return {}
    path = Path(directory) / f"{name}.yaml"
    if not path.exists():
        warnings.append(
            f"Kein Zielprofil {path.name} gefunden. Ohne menschliche "
            f"Bestaetigung bleibt jede Regel, deren Anwendbarkeit auf einer "
            f"Ableitung beruht, auf 'verdaechtig' begrenzt (C4).")
        return {}
    content = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        warnings.append(f"{path.name} contains no target profile — skipped.")
        return {}
    confirmed = _field(content, "confirmed_by_human")
    if confirmed is not None and not isinstance(confirmed, dict):
        warnings.append(f"{path.name}: 'confirmed_by_human' must contain "
                        f"signal name: value — skipped.")
        content["confirmed_by_human"] = {}
        content.pop("bestaetigt_durch_mensch", None)
    return content
