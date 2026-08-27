"""Guarantees about the capture agent that a prompt alone cannot give.

The agent is driven by a model, so most of its behaviour is asked for
rather than enforced. These are the three places where asking is not
enough, and the code has to make the answer impossible:

  no credentials ever leave the loop,
  the browser is the one we say it is,
  an unresolved placeholder is never a measured value.

Static checks on purpose — they must hold without a key, without a
network and without a browser, because that is when somebody would
otherwise be tempted to skip them.
"""

import ast
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.capture import driver

AGENT = pathlib.Path("dpm/capture/agent.py").read_text(encoding="utf-8")
PROMPTS = pathlib.Path("dpm/capture/prompts.py").read_text(encoding="utf-8")
MAIN = pathlib.Path("dpm/capture/main.py").read_text(encoding="utf-8")

print("No account is ever created, no login ever attempted")
# We tell the consumer agency: public pages only, no login, no bypassing of
# access controls — and we will be asked about it in the Q&A. On 24.08. the
# agent carried a full registration pipeline: a throwaway 1secmail address
# and a poll of a third-party inbox for the verification code. The capture
# it produced is a written record of us trying to get past a login wall.
for forbidden, what in [("1secmail", "throwaway mailbox provider"),
                        ("wait_for_email", "inbox polling"),
                        ("get_temp_email", "address generation"),
                        ("aiohttp", "the HTTP client it needed")]:
    assert forbidden not in AGENT, f"{what} is back in agent.py"
print("  ok  no registration machinery in the agent")

# The prompt must not ask for it either, and must say what to do instead.
# Matched on the instruction, not the words: the replacement text says
# "never create an account", which has to be allowed to stand.
for forbidden, what in [("**DO SO**", "comply with a registration prompt"),
                        ("SESSION_EMAIL", "fill in an address"),
                        ("FETCH_OTP", "fetch a verification code"),
                        ("slider, use", "solve a bot challenge")]:
    assert forbidden not in PROMPTS, f"the prompt still tells it to {what}"
assert "NEVER log in" in PROMPTS and "is_blocked=true" in PROMPTS
print("  ok  the prompt stops at the wall instead of stepping over it")

# And if the model asks anyway, the loop refuses rather than complies.
assert 'if "SESSION_EMAIL" in text or "FETCH_OTP" in text:' in AGENT, \
    "nothing intercepts a credential the model asks to type"
refusal = AGENT.split('if "SESSION_EMAIL" in text or "FETCH_OTP" in text:')[1][:900]
assert "decision.is_blocked = True" in refusal and "break" in refusal, \
    "the credential is intercepted but the walk continues"
print("  ok  a credential request ends the walk, it does not get filled in")

print("\nThe browser is configured once, and it is the German one")
# locale was en-US, so amazon.de served the English shop and our German
# keyword rules read "Proceed to Checkout" as an inadmissible order-button
# label. A false accusation manufactured by our own browser setting.
assert driver.LOCALE == "de-DE", driver.LOCALE
assert 'locale="en-US"' not in AGENT and '"locale": "en-US"' not in MAIN
for name in ("LOCALE", "TIMEZONE", "USER_AGENT", "VIEWPORT"):
    assert name in AGENT, f"agent.py does not use the shared {name}"
    assert name in MAIN, f"main.py does not use the shared {name}"
print(f"  ok  {driver.LOCALE} / {driver.TIMEZONE}, taken from driver.py in both")

print("\nThe evidence screenshot is taken before we draw on the page")
# The Beweisakte cites S-xx.png as proof the site looked like this, and
# hashes it as proof of the page state. Markers injected first put our own
# red boxes into both.
tree = ast.parse(AGENT)
walk = next(n for n in ast.walk(tree)
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "visual_explore")
lines = {}
for node in ast.walk(walk):
    if isinstance(node, ast.Call):
        text = ast.get_source_segment(AGENT, node) or ""
        if "inject_som_markers" in text:
            lines.setdefault("marker", node.lineno)
        if "screenshot(path=screenshot_path)" in text:
            lines.setdefault("evidence", node.lineno)
        if "hashlib.sha256" in text and "content()" in text:
            lines.setdefault("hash", node.lineno)
assert lines["evidence"] < lines["marker"], \
    f"markers are injected before the evidence shot: {lines}"
assert lines["hash"] < lines["marker"], \
    f"the hash covers a page we had already drawn on: {lines}"
assert 'os.path.join(output_dir, "nav")' in AGENT, \
    "the marked-up image has no separate home"
# A click that does not replace the document leaves the previous step's
# markers standing, and they were still in the exhibit on 24.08.
cleanup = AGENT.index("forEach(e => e.remove())")
assert cleanup < AGENT.index("screenshot(path=screenshot_path)"), \
    "the previous step's markers are still on the page when the exhibit is taken"
print(f"  ok  evidence at line {lines['evidence']}, markers at {lines['marker']}, "
      f"marked copy into nav/")

print("\nAn unresolved placeholder never becomes a measured value")
# "FETCH:105:checked" was shipped verbatim as a signal: 'checked' was not
# among the resolvable attributes and a bare `except: pass` hid it.
# Scoped to the resolver: the bare except on the page-load wait is a
# genuine "do not care" and predates this.
resolver = AGENT[AGENT.index("# Resolution Logic"):AGENT.index("[*] Agent Thought")]
code = "\n".join(l for l in resolver.splitlines() if not l.strip().startswith("#"))
assert "except: pass" not in code, "the silent except is back in the resolver"
assert '"checked"' in code, "'checked' is still not resolvable"
assert "kein Auswahlfeld" in AGENT, \
    "a non-checkbox would resolve to False instead of an error"
assert "unresolved.append" in AGENT and "all_errors.setdefault" in AGENT, \
    "an unresolvable placeholder is not routed to signal_errors"
# The overlay has to actually collect what the resolver promises.
overlay = AGENT[AGENT.index("map[index] = {"):]
for field in ("area", "fontSize", "contrast", "text", "checked"):
    assert f"{field}:" in overlay[:1000], f"the element map has no {field}"
print("  ok  checked is collected, unresolvable goes to signal_errors")

print("\nA later step may not overwrite a first-contact measurement")
# The consent banner is answered at first contact and gone afterwards.
# Measuring it again on a later page says nothing about the site -- and
# the DOM merge assigned unconditionally, so banner_detected was
# overwritten with the false read off Amazon's sign-in wall and DP-001
# lost its applicability.
assert "supersedes" in AGENT and "from dpm.capture.path import" in AGENT, \
    "agent.py does not use path.supersedes"
# A gap needs the same first-contact protection a value gets: a later
# step reporting "no banner found" is about a banner that was answered.
assert "FIRST_CONTACT" in AGENT, \
    "a later step can still write a first-contact gap"
merge = AGENT[AGENT.index("dom_values, dom_gaps = await collect.measure"):]
assert "supersedes(name," in merge[:900], \
    "the DOM merge still assigns unconditionally"
from dpm.capture.path import supersedes as _sup
assert not _sup("banner_detected", "login_wall", "startseite")
assert _sup("price_listed", "produktdetail", "startseite")
print("  ok  banner signals keep the first contact, funnel signals move down")

print("\nRuns land where rebuild will find them")
# Checked on the default, not on a literal: walk() takes output_root so
# the web UI can start the same run into the same folder.
import inspect
from dpm.capture.main import walk
assert inspect.signature(walk).parameters["output_root"].default == "out", \
    "the default output is not out/"
assert '"capture_mode"' in MAIN and '"industry"' in MAIN, \
    "meta is missing what the Zeitachse and the Marktuebersicht need"
print("  ok  out/<run_id>/, with capture_mode and industry in meta")

print("\nAll capture-agent tests passed.")
