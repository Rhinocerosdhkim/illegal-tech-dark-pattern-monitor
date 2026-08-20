"""One entry point, one output folder, no setup.

    python -m dpm assess data/fixtures/viagogo     findings table
    python -m dpm report data/fixtures/viagogo     Beweisakte as HTML and PDF
    python -m dpm overview data/fixtures/*         Marktuebersicht over many sites
    python -m dpm timeline <earlier> <later>       Zeitachse: two captures compared

Design constraint from AGENDA_Technik.md §6: on Monday a person without a
development background has to operate this alone.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from dpm.engine.rules import load_rules
from dpm.engine.run import load_run
from dpm.engine.verdict import (CLEAR, NOT_APPLICABLE, NO_FINDING, SUSPECTED,
                                UNRESOLVED, assess)
from dpm.report.case_file import build as build_case_file
from dpm.report.diff import build as build_timeline, compare
from dpm.report.overview import build as build_overview, collect

LABEL = {CLEAR: "eindeutig", SUSPECTED: "verdaechtig", UNRESOLVED: "unklar",
         NO_FINDING: "unauffaellig", NOT_APPLICABLE: "nicht anwendbar"}


def _findings(arguments):
    run = load_run(arguments.run)
    rules = load_rules(arguments.rules)
    return run, [assess(rule, run.table) for rule in rules]


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


def cmd_report(arguments) -> int:
    run, findings = _findings(arguments)
    result = build_case_file(run, findings, output=arguments.output,
                             as_pdf=not arguments.html_only)

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
    result = build_overview(overview, output=arguments.output)

    print(f"\nMarktuebersicht — {result['sites']} sites, "
          f"{result['findings']} findings")
    for warning in overview.warnings:
        print(f"  ! {warning}")
    print(f"  {result['html']}")
    print(f"  {result['csv']}\n")
    return 0


def cmd_timeline(arguments) -> int:
    timeline = compare(arguments.earlier, arguments.later,
                       load_rules(arguments.rules))
    result = build_timeline(timeline, output=arguments.output)

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
    print(f"  {result['html']}\n")
    return 0


def _warnings(run) -> None:
    for warning in run.warnings:
        print(f"  ! {warning}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="dpm", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

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
        sub.set_defaults(function=function)

    over = commands.add_parser(
        "overview", help="market overview over several capture runs")
    over.add_argument("runs", type=Path, nargs="+",
                      help="folders containing capture.json")
    over.add_argument("--rules", type=Path, default=None)
    over.add_argument("--output", type=Path, default=Path("out"))
    over.set_defaults(function=cmd_overview)

    tl = commands.add_parser("timeline",
                             help="compare two captures of the same site")
    tl.add_argument("earlier", type=Path, help="the earlier capture run")
    tl.add_argument("later", type=Path, help="the later capture run")
    tl.add_argument("--rules", type=Path, default=None)
    tl.add_argument("--output", type=Path, default=Path("out"))
    tl.set_defaults(function=cmd_timeline)

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
    return 1


if __name__ == "__main__":
    sys.exit(main())
