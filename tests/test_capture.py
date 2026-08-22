"""The capture layer: does it keep the two promises the engine relies on?

    A value we could not read never arrives as 0, false or "". It goes to
    signal_errors, because "measured and absent" and "not checked" are
    different legal statements.

    A step that fails does not take the whole run with it. capture.json is
    written either way, and it is a file the engine can read.

No network and no key: the model is replaced by a stand-in, and the site is
a local HTML file.
"""

import asyncio, json, pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.ai import text_signals
from dpm.ai.client import ModelError
from dpm.capture import driver
from dpm.capture.targets import load as load_target, slug
from dpm.engine.run import load_run

failures = []


def check(condition, message):
    print(f"  {'ok  ' if condition else 'FAIL'}  {message}")
    if not condition:
        failures.append(message)


class FakeModel:
    """Answers whatever the test puts in, or raises."""

    def __init__(self, answer=None, error=None):
        self.answer, self.error = answer, error

    async def ask(self, prompt, schema, screenshot=None):
        if self.error:
            raise ModelError(self.error)
        return self.answer


def read(answer):
    return asyncio.run(text_signals.read(FakeModel(answer), b"", wanted=[
        "countdown_element_present", "scarcity_value", "countdown_text"]))


print("\ntext_signals — typing, confidence, and the never-guess rule")

values, errors = read({"signals": [
    {"name": "countdown_element_present", "value": "true", "confidence": 0.95},
    {"name": "scarcity_value", "value": "3", "confidence": 0.9},
    {"name": "countdown_text", "value": "Angebot endet in 14:59", "confidence": 0.9},
], "not_readable": []})
check(values.get("countdown_element_present") is True, "\"true\" becomes a bool")
check(values.get("scarcity_value") == 3, "\"3\" becomes the number 3")
check(values.get("countdown_text") == "Angebot endet in 14:59", "text stays text")
check(errors == {}, "nothing lands in signal_errors when everything was read")

# _SIGNALE.md: "nur noch wenige verfuegbar" has no number. Reporting 0 would
# mean "measured, zero left" and DP-003 would fire on it.
values, errors = read({"signals": [], "not_readable": [
    {"name": "scarcity_value", "reason": "the note names no number"}]})
check("scarcity_value" not in values, "an unreadable number is not a value")
check("scarcity_value" in errors, "it is in signal_errors instead")
check(values.get("scarcity_value") != 0, "and it is emphatically not 0")

values, errors = read({"signals": [
    {"name": "countdown_element_present", "value": "true", "confidence": 0.3}],
    "not_readable": []})
check("countdown_element_present" not in values,
      "a value below the confidence threshold is not a measurement")
check("countdown_element_present" in errors, "it goes to signal_errors")

values, errors = read({"signals": [
    {"name": "scarcity_value", "value": "nur noch wenige", "confidence": 0.9}],
    "not_readable": []})
check("scarcity_value" not in values,
      "a number that is not a number is refused, not coerced")

values, errors = read({"signals": [
    {"name": "erfundenes_signal", "value": "true", "confidence": 0.9}],
    "not_readable": []})
check(values == {}, "a signal name the rulebook does not know is dropped")
check(len(errors) == 3, "every signal asked for is accounted for")

try:
    asyncio.run(text_signals.read(FakeModel(error="quota exceeded"), b""))
    check(False, "a failing model raises ModelError")
except ModelError:
    check(True, "a failing model raises ModelError")


print("\ndom_hash — stable across two loads of the same page")

volatile = ('<html><body><h1>Angebot</h1>'
            '<script nonce="{n}">var t={n};</script>'
            '<!-- rendered {n} --></body></html>')
check(driver._normalise(volatile.format(n=1))
      == driver._normalise(volatile.format(n=2)),
      "nonces, inline scripts and comments do not change the hash")
check(driver._normalise("<p>a</p>") != driver._normalise("<p>b</p>"),
      "visible markup still does")


print("\ntargets — meta.target has to be the profile name, not the hostname")

check(slug("https://www.viagogo.de/Event/12345") == "viagogo",
      "a URL reduces to the profile name")
check(load_target("https://www.viagogo.de").get("industry") == "Ticketing",
      "and that name finds data/targets/viagogo.yaml")
check(load_target("nicht-vorhanden") == {},
      "a site without a profile is not an error")
check("/" not in slug("file:///tmp/a/shop.html")
      and ":" not in slug("file:///tmp/a/shop.html"),
      "a name that becomes a directory carries no scheme and no slash")


print("\ncapture without a model — still a readable run")

page = pathlib.Path(tempfile.mkdtemp()) / "shop.html"
page.write_text('<html><body style="margin:40px"><h1>Nur noch 2 verfuegbar</h1>'
                '<button>Jetzt bestellen</button></body></html>', encoding="utf-8")

with tempfile.TemporaryDirectory() as tmp:
    run = asyncio.run(driver.capture(page.as_uri(), {"name": "testshop",
                                                     "industry": "Test"},
                                     model=None, output_root=pathlib.Path(tmp)))
    file = run.write()
    check(file.exists(), "capture.json is written even with no model")
    check((run.path / "S-01.png").exists(), "the evidence screenshot is there")

    raw = json.loads(file.read_text())
    check(raw["meta"]["target"] == "testshop", "meta.target is the profile name")
    check(raw["meta"]["locale"] == "de-DE", "the page is loaded in German")
    check(len(raw["steps"]) == 1, "one step captured, then it stops cleanly")
    check(raw["steps"][0]["dom_hash"].startswith("sha256:"), "with a hash")
    # The DOM signals need no model, so they are measured even here. What a
    # model would have read off the screenshot is absent -- and, this is the
    # point, not invented in its place.
    measured = {name: entry["value"] for name, entry in raw["signals"].items()}
    check(measured.get("banner_detected") is False,
          "a missing banner is measured as absent, not guessed")
    check(measured.get("order_button_label") == "Jetzt bestellen",
          "the order button is read out of the DOM")
    check(all({"value", "step", "evidence"} <= set(entry)
              for entry in raw["signals"].values()),
          "every measured signal carries its step and its evidence")
    check(not {"countdown_element_present", "countdown_text", "scarcity_value",
               "scarcity_text_present"} & set(raw["signals"]),
          "nothing a model would have read is invented without one")
    check("third_party_cookies_before_consent" in raw["signal_errors"],
          "what cannot be measured yet says so in signal_errors")

    loaded = load_run(run.path)
    check(loaded.target == "testshop", "the engine reads the file")
    check(loaded.table.errors, "and sees the gaps as gaps")

print("\noff the path — nothing measured there becomes a fact")
# A capture on 22.08. read countdown_element_present=false off a login
# screen and recorded it as a statement about viagogo. The navigator could
# not say anything else: its schema offered only the five path steps, so a
# login wall had to be labelled with one of them. Now it can say "abseits",
# and nothing is attributed to such a page.
from dpm.ai.navigator import _schema
from dpm.capture.path import OFF_PATH, PATH_STEPS

check(OFF_PATH in _schema(PATH_STEPS, OFF_PATH)["properties"]["step"]["enum"],
      "the navigator can say the page is on none of the steps")


class OffPath:
    """A model standing on a login wall, answering honestly."""

    name = backend = "stub"

    async def ask(self, prompt, schema, screenshot=None):
        if "goal_reached" in schema.get("properties", {}):
            return {"step": OFF_PATH, "target_id": None, "goal_reached": True,
                    "reason": "an Anmeldewand, kein Schritt des Trichters"}
        return {"signals": [{"name": "countdown_element_present",
                             "value": "false", "confidence": 0.97}],
                "not_readable": []}


wall = pathlib.Path(tempfile.mkdtemp()) / "login.html"
wall.write_text('<html lang="de"><body><h1>Anmelden</h1>'
                '<input type="password"><button>Anmelden</button></body></html>',
                encoding="utf-8")

with tempfile.TemporaryDirectory() as tmp:
    run = asyncio.run(driver.capture(wall.as_uri(), {"name": "wall"},
                                     model=OffPath(),
                                     output_root=pathlib.Path(tmp)))
    raw = json.loads(run.write().read_text())
    check(raw["signals"] == {},
          "a page off the funnel produces no signal at all")
    check([s["step"] for s in raw["steps"]] == [OFF_PATH],
          "the detour stays visible in the record")
    check(any("not on the path" in n for n in raw["notes"]),
          "and the file says why nothing was measured")
    check("countdown_element_present" not in raw["signal_errors"],
          "nor is it written off as a gap — a later step may still reach it")

print()
if failures:
    print(f"{len(failures)} failed:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("all good\n")
