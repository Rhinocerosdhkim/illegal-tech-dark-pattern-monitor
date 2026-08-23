"""The web app is an addition, never the delivery path.

So the checks are mostly about what it must NOT do: it must not be
required for anything, it must not start two captures at once, and it
must not offer a link to a file that was never written.

No capture is started here — that would open a browser and visit a real
site. What is exercised is the shell around it.
"""

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

print("Without FastAPI the program still says what to do")
from dpm.ui.app import MISSING
assert "rebuild" in MISSING and "out/index.html" in MISSING, MISSING
print("  ok  the message points at the path that needs no server")

try:
    from fastapi.testclient import TestClient
except ImportError:
    print("\n  -   FastAPI not installed — the rest is skipped, which is the "
          "point: nothing else depends on it")
    sys.exit(0)

from dpm.ui.app import create
from dpm.ui.runner import RUNNING, Lauf, Runs

app = create(pathlib.Path("out"))
client = TestClient(app)

print("\nThe Auftrag screen lists what is on disk")
page = client.get("/")
assert page.status_code == 200, page.status_code
assert "Referenzfälle" in page.text and "Prüflauf starten" in page.text
print("  ok  archive and start form")

print("\nA link is only offered for a file that exists")
import re
for href in re.findall(r'href="(/akte/[^"]+)"', page.text):
    answer = client.get(href)
    assert answer.status_code == 200, f"{href} -> {answer.status_code}"
print("  ok  every Akte link resolves")

print("\nEvery view is reachable by clicking, not only by typing a path")
# The Auftrag screen used to link the Beweisakten and nothing else. The
# market overview and the timeline were served but had no link anywhere,
# so the two views that answer "across all targets" were invisible.
links = re.findall(r'href="(/akte/[^"]+)"', page.text)
assert any("marktuebersicht" in href for href in links), \
    "no link to the Marktübersicht"
assert any("zeitachse" in href for href in links), "no link to the Zeitachse"
for href in links:
    assert client.get(href).status_code == 200, href
print(f"  ok  Marktübersicht and Zeitachse linked, {len(links)} links resolve")

print("\nAn empty address is refused")
answer = client.post("/prueflauf", data={"url": "  ", "branche": ""})
assert answer.status_code == 400, answer.status_code
print("  ok  400 rather than a run against nothing")

print("\nAn unknown run says so instead of guessing")
assert client.get("/prueflauf/gibtsnicht").status_code == 404
assert client.get("/prueflauf/gibtsnicht/status").status_code == 404
print("  ok  404 on both")

print("\nOnly one capture at a time")
runs = Runs()
runs._runs["x"] = Lauf(token="x", target="a", industry="", url="https://a.de",
                       output=pathlib.Path("out"), state=RUNNING)
assert runs.busy(), "a running capture was not noticed"
runs._runs["x"].state = "fertig"
assert not runs.busy()
print("  ok  a second target would be refused while one is running")

print("\nProgress is read off the filesystem, not reported")
lauf = Lauf(token="y", target="viagogo", industry="", url="https://viagogo.de",
            output=pathlib.Path("data/fixtures"))
lauf.folder = pathlib.Path("data/fixtures/viagogo")
assert lauf.screenshots == ["S-01.png", "S-02.png", "S-03.png"], lauf.screenshots
print(f"  ok  {len(lauf.screenshots)} captures counted from the folder")

print("\nAll UI tests passed.")
