"""Live capture runs, held in memory while the server is up.

There is no database and no queue: one workstation, one person, one run
at a time. A run that is gone when the server restarts is not a loss —
what matters is on disk in `out/<run_id>/`, and the archive page finds it
again without any of this.

Progress is read off the filesystem rather than reported by the capture
layer. `dpm/capture/` belongs to the other half of the team and this is
not worth a change there: the driver writes `S-01.png`, `S-02.png` … as
it goes, so counting them says which step is running, and `capture.json`
appearing says the run is done.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path

RUNNING = "laeuft"
DONE = "fertig"
FAILED = "fehlgeschlagen"


@dataclass
class Lauf:
    token: str
    target: str
    industry: str
    url: str
    output: Path
    started: float = field(default_factory=time.time)
    state: str = RUNNING
    folder: Path | None = None
    run_id: str | None = None
    note: str = ""
    steps: list = field(default_factory=list)

    @property
    def seconds(self) -> int:
        return int(time.time() - self.started)

    @property
    def screenshots(self) -> list:
        """Captured evidence so far, newest last."""
        if not self.folder or not self.folder.exists():
            return []
        return sorted(p.name for p in self.folder.glob("S-*.png"))

    def find_folder(self) -> Path | None:
        """The run directory the driver created for this run.

        Matched by target and by being newer than the moment we started,
        because the driver builds the run id from its own clock.
        """
        if self.folder:
            return self.folder
        if not self.output.exists():
            return None
        # Both producers end the folder name with a name for the target,
        # but they spell it differently: the driver uses the profile slug
        # ("amazon"), the agent the bare host ("amazon.de"). Matching on
        # the slug alone found neither during an agent run, so the live
        # screen counted zero captures until the run was over.
        for candidate in sorted(self.output.glob("*_*"), reverse=True):
            name = candidate.name.split("_", 1)[-1]
            if self.target not in name and name not in self.target:
                continue
            if (candidate.is_dir()
                    and candidate.stat().st_mtime >= self.started - 5):
                self.folder = candidate
                self.run_id = candidate.name
                return candidate
        return None

    def snapshot(self) -> dict:
        self.find_folder()
        return {"token": self.token, "state": self.state,
                "target": self.target, "industry": self.industry,
                "url": self.url, "seconds": self.seconds,
                "run_id": self.run_id, "note": self.note,
                "screenshots": self.screenshots, "steps": self.steps}


class Runs:
    """Every run this server has started."""

    def __init__(self):
        self._runs: dict = {}
        self._tasks: dict = {}

    def get(self, token: str) -> Lauf | None:
        return self._runs.get(token)

    def latest(self) -> Lauf | None:
        return max(self._runs.values(), key=lambda l: l.started, default=None)

    def busy(self) -> bool:
        """One run at a time — two browsers on one machine skew the timings.

        The polite-retrieval rule we agreed on says the same: never two
        targets in parallel.
        """
        return any(l.state == RUNNING for l in self._runs.values())

    def start(self, lauf: Lauf, coroutine) -> Lauf:
        self._runs[lauf.token] = lauf
        self._tasks[lauf.token] = asyncio.create_task(
            self._supervise(lauf, coroutine))
        return lauf

    async def _supervise(self, lauf: Lauf, coroutine) -> None:
        try:
            await coroutine
        except Exception as error:                    # capture, browser, disk
            lauf.state = FAILED
            lauf.note = f"{type(error).__name__}: {error}"
        else:
            lauf.state = DONE
        finally:
            lauf.find_folder()
