"""The Marktübersicht is the second output the consumer agency asked for:
"Tabelle mit Filtermöglichkeit und Statistiken (Branche, Art), Norm
klassifizieren".

What matters here is that the aggregation says the same thing as the
individual assessments. A market overview that quietly disagrees with the
evidence files it is built from would be worse than none at all.
"""

import csv, sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from dpm.engine.rules import load_rules
from dpm.engine.run import load_run
from dpm.engine.verdict import assess
from dpm.report.overview import CSV_COLUMNS, build, collect, statistics

RULES = load_rules()
FOLDERS = ["data/fixtures/viagogo", "data/fixtures/sauberer-shop",
           "data/fixtures/ratgeber-portal"]

overview = collect(FOLDERS, RULES)

assert len(overview.sites) == 3, overview.sites
assert len(overview.rows) == 3 * len(RULES), len(overview.rows)
print(f"  ok  {len(overview.sites)} sites × {len(RULES)} rules = {len(overview.rows)} rows")

print("\nThe aggregation agrees with the individual assessments")
for folder in FOLDERS:
    run = load_run(folder)
    single = {f.rule.id: f.level for f in (assess(r, run.table) for r in RULES)}
    aggregated = {r.rule_id: r.level for r in overview.rows if r.target == run.target}
    assert single == aggregated, f"{run.target}: {single} != {aggregated}"
    print(f"  ok  {run.target}")

print("\nOnly findings are counted, not silence")
findings = overview.findings
assert all(f.level in ("eindeutig", "verdaechtig", "unklar") for f in findings)
assert len(findings) < len(overview.rows), "unauffaellig/nicht anwendbar leaked in"
print(f"  ok  {len(findings)} findings out of {len(overview.rows)} rows")

print("\nStatistics")
stats = statistics(overview)
for key in ("by_industry", "by_category", "by_norm", "by_level"):
    assert key in stats, key
assert sum(e["count"] for e in stats["by_industry"]) == len(findings), \
    "the industry breakdown does not add up to the findings"
assert sum(e["count"] for e in stats["by_level"]) == len(overview.rows), \
    "the level breakdown must cover every row, including the silent ones"
print("  ok  breakdowns add up")

# The industry column is what the consumer agency explicitly asked for. If it
# is empty the whole statistic is worthless, so it must never silently be "—".
assert all(r.industry and r.industry != "—" for r in overview.rows), \
    "a capture run without an industry"
print("  ok  every row carries an industry")

print("\nHTML and CSV")
with tempfile.TemporaryDirectory() as tmp:
    result = build(overview, output=tmp)
    html = result["html"].read_text(encoding="utf-8")

    for needle, name in [("Marktübersicht", "title"),
                         ("zurücksetzen", "filter reset"),
                         ('id="f-branche"', "industry filter"),
                         ('id="f-kategorie"', "category filter"),
                         ('id="f-norm"', "provision filter"),
                         ("Erfassungsläufe", "per-run totals"),
                         ("keine rechtliche Feststellung", "disclaimer")]:
        assert needle in html, f"missing from the overview: {name}"
        print(f"  ok  {name}")

    with result["csv"].open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0]) == CSV_COLUMNS, list(rows[0])
    assert len(rows) == len(overview.rows)
    print(f"  ok  CSV: {len(rows)} rows, {len(CSV_COLUMNS)} columns")

print("\nA single site also works")
one = collect(["data/fixtures/viagogo"], RULES)
with tempfile.TemporaryDirectory() as tmp:
    assert build(one, output=tmp)["sites"] == 1
print("  ok  overview over one run")

print("\nAll overview tests passed.")
