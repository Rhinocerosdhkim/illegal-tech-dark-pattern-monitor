"""What the two model call sites are allowed to put into a document.

Neither of them is trusted. AI (4) writes a paragraph into the Beweisakte,
AI (2) proposes sites to visit — both are checked against their input and
dropped when they do not hold up. These tests are about the checks, so
they run without a key and without a network: the model is a stub.
"""

import asyncio
import sys
import pathlib
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.ai import doc_import, narrative
from dpm.ai.client import ModelError


class Stub:
    """A model that answers whatever the test tells it to."""

    def __init__(self, answer=None, error=None):
        self.answer, self.error = answer, error

    async def ask(self, prompt, schema, screenshot=None):
        if self.error:
            raise ModelError(self.error)
        return self.answer


GIVEN = {"rule_id": "DP-001", "rule_name": "Consent-Buttons",
         "norm": "§ 25 Abs. 1 TDDDG", "level": "verdaechtig",
         "measurements": [("reject_click_depth", "3"),
                          ("accept_button_area_px2", "4200"),
                          ("banner_detected", "ja")]}

print("AI 4 — a summary may only repeat what was measured")
for text, expected, why in [
        ("Die Ablehnung erforderte 3 Interaktionsschritte; die "
         "Zustimmen-Schaltfläche maß 4200 px².", True, "measured values"),
        ("Die Ablehnung erforderte 7 Interaktionsschritte.", False,
         "invented number"),
        ("Das Banner ist rechtswidrig.", False, "asserts a violation"),
        ("Der Wert banner_wackelt lag bei 3.", False, "invented signal"),
        ("Gemessen nach § 25 Abs. 1 TDDDG.", True, "digits of the provision"),
        ("x" * (narrative.MAX_CHARS + 1), False, "too long"),
        ("   ", False, "empty")]:
    draft = narrative.check(text, GIVEN)
    kept = draft.text is not None
    assert kept is expected, f"{why}: {draft.rejected or draft.text!r}"
    print(f"  ok  {'kept  ' if kept else 'droppd'}  {why}")

print("\nAI 4 — a model that fails costs the report nothing")
draft = asyncio.run(narrative.summarise(Stub(error="quota exceeded"), GIVEN))
assert draft.text is None and "quota" in draft.rejected
print("  ok  reported as rejected, not raised")

print("\nAI 4 — the whole answer goes, not the bad sentence")
draft = asyncio.run(narrative.summarise(
    Stub({"text": "Die Ablehnung erforderte 3 Schritte. "
                  "Das ist rechtswidrig."}), GIVEN))
assert draft.text is None, "a violation claim survived because of a good half"
print("  ok  no partial acceptance")

DOCUMENT = ("Kandidaten Q3\nviagogo.de\tTickets\n"
            "www.beispielshop.de\tKleidung\neventim-resale.de\tTickets\n")

print("\nAI 2 — every address has to occur in the document")
kept, dropped = doc_import.verify(
    [{"url": "https://www.viagogo.de", "branche": "Ticketing"},
     {"url": "https://erfunden.de", "branche": "Mode"},
     {"url": "viagogo.de", "branche": "Ticketing"},
     {"url": "https://beispielshop.de", "branche": "Nichtsdergleichen"},
     {"url": "nonsens", "branche": "Mode"}],
    DOCUMENT)
hosts = [k["host"] for k in kept]
assert hosts == ["viagogo.de", "beispielshop.de"], hosts
assert len(dropped) == 2, dropped
print(f"  ok  {len(kept)} kept, {len(dropped)} dropped, duplicate removed")

print("\nAI 2 — an invented industry costs the industry, not the target")
assert [k["branche"] for k in kept] == ["Ticketing", ""], kept
print("  ok  address survives with the industry left open for a person")

print("\nAI 2 — www is a prefix, not a set of characters")
assert doc_import.host("wow-shop.de") == "wow-shop.de"
assert doc_import.host("https://www.viagogo.de/Event/1") == "viagogo.de"
print("  ok  wow-shop.de stays intact")

print("\nAI 2 — text comes out of csv, docx and xlsx without extra packages")
with tempfile.TemporaryDirectory() as tmp:
    csv_file = pathlib.Path(tmp) / "ziele.csv"
    csv_file.write_text(DOCUMENT, encoding="utf-8")
    assert "viagogo.de" in doc_import.text_of(csv_file)
    print("  ok  csv")

    import zipfile
    docx = pathlib.Path(tmp) / "ziele.docx"
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr("word/document.xml",
                         "<w:p><w:t>viagogo.de</w:t></w:p>")
    assert "viagogo.de" in doc_import.text_of(docx)
    print("  ok  docx")

    try:
        doc_import.text_of(pathlib.Path(tmp) / "ziele.pdf")
    except ValueError as error:
        assert "wird nicht" in str(error)
        print("  ok  an unsupported format says so instead of guessing")

print("\nAll AI guard tests passed.")
