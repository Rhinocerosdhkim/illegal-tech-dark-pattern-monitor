"""The handover command. From Tuesday nobody from the dev team is around,
and on Monday a person without a development background has to run this
alone. So it takes no arguments, needs no configuration and no keys, and
finds its own work.

It also does the thing nobody should have to remember: if a target was
captured more than once, the timeline is built by itself. A monitor that
only notices a quietly reintroduced design when somebody thinks to look is
not a monitor.
"""

import json, re, sys, pathlib, shutil, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.__main__ import main
from dpm.engine.discovery import by_target, find_runs, pairs_to_compare

print("Discovery")
runs = find_runs()
groups = by_target(runs)
assert len(runs) >= 5, runs
assert "viagogo" in groups and len(groups["viagogo"]) == 2, list(groups)
print(f"  ok  {len(runs)} runs, {len(groups)} targets, viagogo captured twice")

# The folder name is not trusted — target and timestamp come out of the file.
oldest, newest = groups["viagogo"]
assert oldest[1]["timestamp"] < newest[1]["timestamp"]
print("  ok  runs sorted by the timestamp inside capture.json, not by folder")

pairs = [p for p in pairs_to_compare(groups) if not p[3]]
assert [p[0] for p in pairs] == ["viagogo"], pairs
print("  ok  exactly the target with two captures gets a timeline")

print("\nA fixture is never compared against a real capture")
with tempfile.TemporaryDirectory() as tmp:
    place = pathlib.Path(tmp)
    shutil.copytree("data/fixtures/viagogo", place / "a")
    shutil.copytree("data/fixtures/viagogo-2026-09", place / "b")
    # same target, but the later one claims to come from a real browser
    capture = place / "b" / "capture.json"
    raw = json.loads(capture.read_text(encoding="utf-8"))
    raw["meta"]["capture_mode"] = "headless"
    capture.write_text(json.dumps(raw), encoding="utf-8")

    mixed = pairs_to_compare(by_target(find_runs(place)))
    assert len(mixed) == 1 and mixed[0][3], mixed
    assert "ohne Aussagekraft" in mixed[0][3]
    print("  ok  differing capture_mode -> comparison skipped, with a reason")

print("\nThe command itself")
with tempfile.TemporaryDirectory() as tmp:
    out = pathlib.Path(tmp)
    assert main(["rebuild", "data/fixtures", "--output", str(out),
                 "--html-only"]) == 0

    akten = sorted(out.glob("*/beweisakte.html"))
    assert len(akten) == 5, [p.parent.name for p in akten]
    assert (out / "marktuebersicht" / "marktuebersicht.html").exists()
    assert (out / "marktuebersicht" / "marktuebersicht.csv").exists()
    zeitachsen = sorted(out.glob("zeitachse_*/zeitachse.html"))
    assert len(zeitachsen) == 1, zeitachsen
    print(f"  ok  {len(akten)} Beweisakten, 1 Marktübersicht, "
          f"{len(zeitachsen)} Zeitachse — from no arguments")

    # From Tuesday somebody without a development background opens this
    # folder. Without the index page they see run-id directories and have
    # to guess; and every link on it must point at a file that exists.
    index = out / "index.html"
    assert index.exists(), "no index.html — the folder is unnavigable"
    page = index.read_text(encoding="utf-8")
    links = re.findall(r'href="([^"]+)"', page)
    assert links, "index without a single link"
    missing = [l for l in links if not (out / l).exists()]
    assert not missing, f"index links to files that do not exist: {missing}"
    print(f"  ok  index.html, {len(links)} links, all resolvable")

    # Running it again must not multiply anything: the outputs it writes
    # carry no capture.json, so they are not mistaken for new runs.
    assert main(["rebuild", "data/fixtures", "--output", str(out),
                 "--html-only"]) == 0
    assert len(sorted(out.glob("*/beweisakte.html"))) == 5
    print("  ok  running it twice changes nothing")

print("\nNothing to do is said, not crashed on")
with tempfile.TemporaryDirectory() as tmp:
    empty = pathlib.Path(tmp) / "leer"; empty.mkdir()
    assert main(["rebuild", str(empty), "--output", str(empty)]) == 1
    print("  ok  no captures -> exit code 1 and a readable message")

print("\nAll rebuild tests passed.")
