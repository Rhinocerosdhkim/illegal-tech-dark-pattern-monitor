"""One entry point, one output folder, no setup.

    python -m dpm capture viagogo                  capture a site into out/
    python -m dpm assess data/fixtures/viagogo     findings table
    python -m dpm report data/fixtures/viagogo     Beweisakte as HTML and PDF
    python -m dpm overview data/fixtures/*         Marktuebersicht over many sites
    python -m dpm timeline <earlier> <later>       Zeitachse: two captures compared
    python -m dpm zielliste <datei>                document with links -> target list
    python -m dpm gold                             accuracy against the gold standard
    python -m dpm rebuild                          rebuild EVERY output, no arguments
    python -m dpm ui                               local web app on 127.0.0.1:8000

Both accept --pdf. The market overview additionally takes --branche,
--kategorie, --stufe and --norm: the PDF is then printed with those filters
applied, so the document shows exactly the view somebody selected.

Design constraint from AGENDA_Technik.md §6: on Monday a person without a
development background has to operate this alone.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import yaml

from dpm.engine.discovery import by_target, find_runs, pairs_to_compare
from dpm.engine.rules import load_rules
from dpm.engine.run import load_run
from dpm.engine.verdict import (CLEAR, NOT_APPLICABLE, NO_FINDING, SUSPECTED,
                                UNRESOLVED, assess)
from dpm.ai.client import Model, ModelError, unavailable as model_unavailable
from dpm.ai.doc_import import read_targets, write as write_targets
from dpm.ai.narrative import facts as narrative_facts, summarise
from dpm.report.archive import build as build_archive, relative
from dpm.report.gold import (GOLD, compare as compare_gold,
                             rate as gold_rate, read as read_gold)
from dpm.report.case_file import build as build_case_file
from dpm.report.diff import build as build_timeline, compare
from dpm.report.overview import build as build_overview, collect

LABEL = {CLEAR: "eindeutig", SUSPECTED: "verdaechtig", UNRESOLVED: "unklar",
         NO_FINDING: "unauffaellig", NOT_APPLICABLE: "nicht anwendbar"}


def _findings(arguments):
    run = load_run(arguments.run)
    rules = load_rules(arguments.rules)
    return run, [assess(rule, run.table) for rule in rules]


def cmd_capture(arguments) -> int:
    from dpm.ai.client import Model, unavailable
    from dpm.capture.driver import capture
    from dpm.capture.targets import load as load_target, slug

    profile = load_target(arguments.target)
    url = arguments.url or profile.get("start")
    if not url:
        print(f"\nNo start URL. Either give one, or add a profile with a "
              f"'start:' entry as data/targets/{arguments.target}.yaml\n",
              file=sys.stderr)
        return 1
    if not profile:
        profile = {"name": slug(arguments.target)}

    # No model is not a failure. The start page, its screenshot and its hash
    # are still evidence, and every signal simply lands in signal_errors.
    model, reason = None, unavailable()
    if reason:
        print(f"\n  ! no model available: {reason}")
        print("    start page only, no navigation — the signals measured "
              "in the DOM are still taken")
    else:
        model = Model.open()
        print(f"\nModel     {model.name}  ({model.backend})")

    run = asyncio.run(capture(url, profile, model,
                              output_root=arguments.output,
                              max_steps=arguments.steps))
    file = run.write()

    print(f"\nTarget    {run.meta['target']}  ({run.meta['industry']})")
    print(f"Path      " + " -> ".join(s["step"] for s in run.steps))
    print(f"Signals   {len(run.signals)} measured, "
          f"{len(run.errors)} not captured")
    for note in run.notes:
        print(f"  ! {note}")
    print(f"\n  {file}")
    print(f"\nNext:  python -m dpm assess {run.path}\n")
    return 0


def cmd_assess(arguments) -> int:
    run, findings = _findings(arguments)

    print(f"\nTarget    {run.target}  ({run.industry})")
    print(f"Capture   {run.meta.get('timestamp')}   {run.run_id}")
    print(f"Signals   {len(run.table.values)} measured, "
          f"{len(run.table.errors)} not captured")
    _warnings(run)
    print()

    header = f"{'Rule':8} {'Category':13} {'Level':15} {'Status':8} Pattern"
    print(header)
    print("-" * len(header))
    for f in findings:
        print(f"{f.rule.id:8} {f.rule.category:13} "
              f"{LABEL[f.level]:15} {f.rule.status:8} {f.rule.name[:44]}")

    for f in findings:
        if not f.reportable:
            continue
        print(f"\n── {f.rule.id} · {LABEL[f.level].upper()} "
              f"{'(downgraded)' if f.downgraded else ''}")
        print(f"   Provision  {f.rule.norm}")
        if f.would_be_level:
            print(f"   Would be   {LABEL[f.would_be_level]} — applicability "
                  f"could not be checked")
        if f.condition:
            print(f"   Condition  {f.condition}")
        for e in f.evidence:
            print(f"   Evidence   {e['signal']} = {e['value']!r}"
                  f"   [{e['step']} · {e['evidence']}]")
        for gap in f.unresolved:
            print(f"   Not captured   {gap['signal']} — {gap['reason']}")
        for note in f.notes:
            print(f"   Note       {note}")

    counts = {level: sum(1 for f in findings if f.level == level) for level in LABEL}
    print("\n" + "  ".join(f"{LABEL[l]}: {n}" for l, n in counts.items() if n))
    print()
    return 0


def _summaries(findings: list) -> dict:
    """AI (4): one machine-formulated paragraph per finding.

    Off unless asked for. The document handed over on Monday contains no
    model-written sentence at all, and that is a claim we have to be able
    to make without qualification.
    """
    reason = model_unavailable()
    if reason:
        print(f"\n  ! Zusammenfassungen uebersprungen — {reason}")
        return {}

    model = Model.open()
    texts, verworfen = {}, []

    async def run_all():
        for finding in findings:
            if not finding.reportable:
                continue
            draft = await summarise(model,
                                    narrative_facts(finding,
                                                    LABEL[finding.level]))
            if draft.text:
                texts[finding.rule.id] = draft.text
            else:
                verworfen.append((finding.rule.id, draft.rejected))

    asyncio.run(run_all())
    for rule_id, grund in verworfen:
        print(f"  ! {rule_id}: Zusammenfassung verworfen — {grund}")
    return texts


def cmd_report(arguments) -> int:
    run, findings = _findings(arguments)
    summaries = _summaries(findings) if arguments.zusammenfassung else None
    result = build_case_file(run, findings, output=arguments.output,
                             as_pdf=not arguments.html_only,
                             summaries=summaries)

    print()
    _warnings(run)
    print(f"\nBeweisakte {run.target} — {result.finding_count} findings")
    print(f"  {result.html}")
    if result.pdf:
        print(f"  {result.pdf}  ({result.pdf.stat().st_size // 1024} kB)")
    else:
        print("  (no PDF — Playwright not available)")
    print()
    return 0


def cmd_overview(arguments) -> int:
    overview = collect(arguments.runs, load_rules(arguments.rules))
    selection = {"branche": arguments.branche, "kategorie": arguments.kategorie,
                 "stufe": arguments.stufe, "norm": arguments.norm}
    result = build_overview(overview, output=arguments.output,
                            as_pdf=arguments.pdf or any(selection.values()),
                            selection=selection)

    print(f"\nMarktuebersicht — {result['sites']} sites, "
          f"{result['findings']} findings")
    for warning in overview.warnings:
        print(f"  ! {warning}")
    chosen = "  ".join(f"{k}={v}" for k, v in selection.items() if v)
    if chosen:
        print(f"  Filter    {chosen}")
    print(f"  {result['html']}")
    print(f"  {result['csv']}")
    if result["pdf"]:
        print(f"  {result['pdf']}")
    print()
    return 0


def cmd_timeline(arguments) -> int:
    timeline = compare(arguments.earlier, arguments.later,
                       load_rules(arguments.rules))
    result = build_timeline(timeline, output=arguments.output,
                            as_pdf=arguments.pdf)

    print(f"\nZeitachse {timeline.later.target} — {timeline.days_between}")
    for warning in timeline.warnings:
        print(f"  ! {warning}")

    if not timeline.noteworthy:
        print("\n  Keine Veraenderung an den Befunden.")
    for change in timeline.noteworthy:
        print(f"\n  {change.rule_id}  {LABEL[change.before_level]} -> "
              f"{LABEL[change.after_level]}   [{change.kind}]")
        print(f"    {change.rule_name[:66]}")
        if change.note:
            print(f"    {change.note[:120]}")

    changed = [s for s in timeline.signal_changes if s.kind == "geaendert"]
    print(f"\n  {len(changed)} Messwerte geaendert, "
          f"{sum(1 for s in timeline.step_changes if s.changed)} Seitenzustaende")
    print(f"  {result['html']}")
    if result["pdf"]:
        print(f"  {result['pdf']}")
    print()
    return 0


def cmd_rebuild(arguments) -> int:
    """Regenerate every output from the captures already on disk.

    The handover command. No arguments, no configuration, no keys — on
    Monday a person without a development background has to be able to run
    this, and from Tuesday nobody from the dev team is available. Karthik
    re-captures a site on Wednesday, runs this, and the presentation
    material is current.

    It also does what nobody should have to remember: if a target was
    captured more than once, the timeline is built by itself.
    """
    rules = load_rules(arguments.rules)
    runs = find_runs(*arguments.places) if arguments.places else find_runs()
    if not runs:
        print("\nKeine Erfassungen gefunden. Erwartet werden Ordner mit einer "
              "capture.json darin, unter out/ oder data/fixtures/.\n",
              file=sys.stderr)
        return 1

    groups = by_target(runs)
    print(f"\n{len(runs)} Erfassungen, {len(groups)} Ziele\n")

    folder = Path(arguments.output)
    akten = []

    print("Beweisakten")
    built = 0
    for path in runs:
        run = load_run(path)
        findings = [assess(rule, run.table) for rule in rules]
        result = build_case_file(run, findings, output=arguments.output,
                                 as_pdf=not arguments.html_only)
        built += 1
        counts = {}
        for finding in findings:
            if finding.reportable:
                counts[finding.level] = counts.get(finding.level, 0) + 1
        akten.append({"target": run.target, "industry": run.industry,
                      "timestamp": run.meta.get("timestamp"),
                      "run_id": run.run_id, "counts": counts,
                      "findings": result.finding_count,
                      "html": relative(result.html, folder),
                      "pdf": relative(result.pdf, folder)})
        print(f"  {run.target:22} {result.finding_count} Befunde   "
              f"{result.pdf or result.html}")

    print("\nMarktuebersicht")
    overview = collect(runs, rules)
    result = build_overview(overview, output=arguments.output,
                            as_pdf=not arguments.html_only)
    print(f"  {result['sites']} Seiten, {result['findings']} Befunde   "
          f"{result['pdf'] or result['html']}")
    uebersicht = {"sites": result["sites"], "findings": result["findings"],
                  "html": relative(result["html"], folder),
                  "csv": relative(result["csv"], folder),
                  "pdf": relative(result["pdf"], folder)}

    print("\nZeitachsen")
    zeitachsen = []
    pairs = pairs_to_compare(groups)
    if not pairs:
        print("  keine — kein Ziel wurde bisher zweimal erfasst")
    for target, earlier, later, note in pairs:
        if note:
            print(f"  ! {note}")
            continue
        timeline = compare(earlier, later, rules)
        result = build_timeline(timeline, output=arguments.output,
                                as_pdf=not arguments.html_only)
        wording = (f"{result['changes']} Veraenderung(en)" if result["changes"]
                   else "keine Veraenderung")
        zeitachsen.append({"target": target, "spanne": timeline.days_between,
                           "changes": result["changes"],
                           "html": relative(result["html"], folder),
                           "pdf": relative(result["pdf"], folder)})
        print(f"  {target:22} {timeline.days_between}   {wording}   "
              f"{result['pdf'] or result['html']}")

    index = build_archive(akten, uebersicht, zeitachsen,
                          output=arguments.output)
    print(f"\nUebersichtsseite\n  {index}")

    print(f"\nFertig. Alles liegt unter {folder.resolve()}")
    print(f"Zum Ansehen: {index} im Browser oeffnen.\n")
    return 0


def cmd_ui(arguments) -> int:
    """Serve the three views and, unlike the files, allow starting a run.

    An addition, never the delivery path: everything it shows also exists
    as a file under out/ and opens without any server.
    """
    from dpm.ui.app import serve
    return serve(host=arguments.host, port=arguments.port,
                 output=arguments.output)


def cmd_zielliste(arguments) -> int:
    """AI (2): a document with links becomes a target list.

    The model proposes; every address it names has to occur in the
    document, and the list is written for a person to correct. Nothing
    here starts a capture.
    """
    reason = model_unavailable()
    if reason:
        print(f"\n{reason}\n", file=sys.stderr)
        return 1

    try:
        targets, dropped = asyncio.run(
            read_targets(Model.open(), arguments.file))
    except (ModelError, ValueError, OSError) as error:
        print(f"\n{error}\n", file=sys.stderr)
        return 1

    if not targets:
        print(f"\nIn {arguments.file} wurde keine verwertbare Adresse "
              f"gefunden.\n", file=sys.stderr)
        return 1

    path = write_targets(targets, arguments.output)
    print(f"\nZielliste aus {arguments.file}\n")
    print(f"{'Adresse':40} Branche")
    print("-" * 60)
    for target in targets:
        print(f"{target['url'][:39]:40} {target['branche'] or '— offen'}")

    if dropped:
        print(f"\nVerworfen ({len(dropped)}):")
        for entry in dropped:
            print(f"  {entry.get('url', '?')[:39]:40} {entry['grund']}")

    print(f"\n{path}")
    print("Bitte durchsehen und die offenen Branchen ergaenzen; die Spalte "
          "geprueft_von_mensch danach auf ja setzen.\n")
    return 0


def cmd_gold(arguments) -> int:
    """Compare the system's verdicts against the hand-written gold standard.

    The number the consumer agency asks for first is not how much we find,
    it is how often we are wrong about a site where there is nothing. That
    is why the false-alarm rate is printed against the clean rows only.
    """
    gold_rows = read_gold(arguments.file)
    if not gold_rows:
        print(f"\n{arguments.file} enthaelt noch keine bewerteten Zeilen.\n"
              f"Ohne Menschenbefunde gibt es keine Treffsicherheit zu messen "
              f"(siehe data/gold-standard/README.md).\n", file=sys.stderr)
        return 1

    rules = load_rules(arguments.rules)
    paths = find_runs(*arguments.runs) if arguments.runs else find_runs()
    runs = [load_run(path) for path in paths]
    overview = collect(paths, rules)
    result = compare_gold(gold_rows, overview.rows, runs)

    print(f"\nGold Standard — System gegen Mensch")
    print(f"Datei     {arguments.file}")
    print(f"Zeilen    {len(gold_rows)} bewertet, "
          f"{len(result.uncovered)} ohne Erfassung, "
          f"{len(result.unreadable)} unlesbar")
    if result.fixtures_ignored:
        print(f"          {result.fixtures_ignored} Fixture(s) uebergangen — "
              f"handgeschrieben, keine Messung")
    print()

    print(f"Verglichen            {len(result.rows)}")
    print(f"  nicht messbar       {gold_rate(result.unresolved, result.rows)}"
          f"   unklar — weder Treffer noch Fehler")
    print(f"  entschieden         {len(result.decided)}")
    print(f"    uebereinstimmend  {gold_rate(result.agreed, result.decided)}")
    print(f"    Fehlalarm         {gold_rate(result.false_alarms, result.clean)}"
          f"   von den Seiten, auf denen der Mensch nichts fand")
    print(f"    uebersehen        "
          f"{gold_rate(result.missed, result.flagged_by_human)}"
          f"   von den Seiten, auf denen der Mensch etwas fand")

    if result.deviations:
        print("\nAbweichungen im Einzelnen")
        for row in result.deviations:
            print(f"  {row['site']:24} {row['rule']:8} "
                  f"Mensch {LABEL[row['human']]:14} "
                  f"System {LABEL[row['system']]}")
            if row["note"]:
                print(f"    {row['note']}")

    if result.uncovered:
        print("\nOhne Erfassung — nicht verglichen")
        for row in result.uncovered:
            print(f"  {row['site']:24} {row['rule']:8} "
                  f"Mensch {LABEL[row['human']]}")

    if result.unreadable:
        print(f"\n{len(result.unreadable)} Zeile(n) unlesbar — url, "
              f"pattern_id und befund_mensch muessen gefuellt sein")

    print()
    return 0


def _warnings(run) -> None:
    for warning in run.warnings:
        print(f"  ! {warning}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="dpm", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    cap = commands.add_parser(
        "capture", help="capture a site and write out/<run_id>/capture.json")
    cap.add_argument("target", help="a name from data/targets/, or a URL")
    cap.add_argument("--url", default=None,
                     help="start URL, if the target has no profile")
    cap.add_argument("--output", type=Path, default=Path("out"))
    cap.add_argument("--steps", type=int, default=6,
                     help="how many path steps at most")
    cap.set_defaults(function=cmd_capture)

    for name, help_text, function in [
            ("assess", "check a capture run against the rulebook", cmd_assess),
            ("report", "build the Beweisakte as HTML and PDF", cmd_report)]:
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("run", type=Path, help="folder containing capture.json")
        sub.add_argument("--rules", type=Path, default=None)
        if name == "report":
            sub.add_argument("--output", type=Path, default=Path("out"))
            sub.add_argument("--html-only", action="store_true",
                             dest="html_only", help="skip the PDF, for quick runs")
            sub.add_argument("--zusammenfassung", action="store_true",
                             help="machine-formulated paragraph per finding "
                                  "(AI 4); needs a model key")
        sub.set_defaults(function=function)

    over = commands.add_parser(
        "overview", help="market overview over several capture runs")
    over.add_argument("runs", type=Path, nargs="+",
                      help="folders containing capture.json")
    over.add_argument("--rules", type=Path, default=None)
    over.add_argument("--output", type=Path, default=Path("out"))
    over.add_argument("--pdf", action="store_true",
                      help="also print a PDF of the table")
    for name, helptext in [("branche", "e.g. Ticketing"),
                           ("kategorie", "e.g. Zeitdruck"),
                           ("stufe", "eindeutig | verdaechtig | unklar"),
                           ("norm", "provision as shown in the table")]:
        over.add_argument(f"--{name}", default=None,
                          help=f"print the PDF filtered by {name} ({helptext})")
    over.set_defaults(function=cmd_overview)

    tl = commands.add_parser("timeline",
                             help="compare two captures of the same site")
    tl.add_argument("earlier", type=Path, help="the earlier capture run")
    tl.add_argument("later", type=Path, help="the later capture run")
    tl.add_argument("--rules", type=Path, default=None)
    tl.add_argument("--output", type=Path, default=Path("out"))
    tl.add_argument("--pdf", action="store_true", help="also print a PDF")
    tl.set_defaults(function=cmd_timeline)

    ui = commands.add_parser(
        "ui", help="local web app: archive, live run, results")
    ui.add_argument("--host", default="127.0.0.1")
    ui.add_argument("--port", type=int, default=8000)
    ui.add_argument("--output", type=Path, default=Path("out"))
    ui.set_defaults(function=cmd_ui)

    zl = commands.add_parser(
        "zielliste", help="read a document with links into a target list (AI 2)")
    zl.add_argument("file", type=Path, help="csv, txt, xlsx or docx")
    zl.add_argument("--output", type=Path, default=Path("out/zielliste.csv"))
    zl.set_defaults(function=cmd_zielliste)

    gold = commands.add_parser(
        "gold", help="system verdicts against the hand-written gold standard")
    gold.add_argument("runs", type=Path, nargs="*",
                      help="where to look for captures; default: out/ and "
                           "data/fixtures/")
    gold.add_argument("--file", type=Path, default=GOLD,
                      help="the gold standard CSV")
    gold.add_argument("--rules", type=Path, default=None)
    gold.set_defaults(function=cmd_gold)

    rb = commands.add_parser(
        "rebuild", help="rebuild every output from the captures on disk")
    rb.add_argument("places", type=Path, nargs="*",
                    help="where to look; default: out/ and data/fixtures/")
    rb.add_argument("--rules", type=Path, default=None)
    rb.add_argument("--output", type=Path, default=Path("out"))
    rb.add_argument("--html-only", action="store_true", dest="html_only",
                    help="skip the PDFs, for quick runs")
    rb.set_defaults(function=cmd_rebuild)

    arguments = parser.parse_args(argv)

    # Error messages have to be actionable for someone who does not develop:
    # from Tuesday nobody from the dev team is available.
    try:
        return arguments.function(arguments)
    except FileNotFoundError as error:
        print(f"\nFile not found: {error}\n"
              f"Expected a folder with a capture.json inside.\n", file=sys.stderr)
    except json.JSONDecodeError as error:
        print(f"\ncapture.json is not readable (line {error.lineno}): "
              f"{error.msg}\n", file=sys.stderr)
    except yaml.YAMLError as error:
        print(f"\nA YAML file is not readable:\n{error}\n", file=sys.stderr)
    except ImportError as error:
        print(f"\nA package is missing: {error}\n"
              f"Install it with:  .venv/bin/pip install -r requirements.txt\n",
              file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
