"""Marktübersicht — many sites, filterable, with statistics.

The second output, from the same capture data as the Beweisakte. The
consumer agency asked for it in the seminar of 19.08. in these words:
"Tabelle (z. B. PDF) mit Filtermöglichkeit und Statistiken (Branche, Art),
Norm klassifizieren".

Where the Beweisakte serves one procedure against one company, this serves
market observation: which industries stand out, which pattern is the most
common, which provision is invoked most often, and what changed since the
last capture.

Deliberately no database. One capture run is one JSON file; the overview is
an aggregation over a handful of them, computed on the fly.

The rendered page is German — same reason as the Beweisakte. The code is
English.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dpm import PRODUCT_NAME
from dpm.engine.rules import load_rules
from dpm.engine.run import load_run
from dpm.engine.verdict import (CLEAR, NOT_APPLICABLE, NO_FINDING, SUSPECTED,
                                UNRESOLVED, assess)
from dpm.report.case_file import CATEGORY_LABEL, LEVEL_LABEL, _environment
from dpm.report.pdf import apply_filters, render as render_pdf

# Order matters: it is the order of the summary and of the filter buttons.
LEVEL_ORDER = [CLEAR, SUSPECTED, UNRESOLVED, NO_FINDING, NOT_APPLICABLE]

CSV_COLUMNS = ["target", "industry", "timestamp", "run_id", "rule_id",
               "rule_name", "category", "norm", "level", "status",
               "condition", "evidence"]


@dataclass
class Row:
    target: str
    industry: str
    timestamp: str
    run_id: str
    rule_id: str
    rule_name: str
    category: str
    norm: str
    level: str
    status: str
    condition: str = ""
    evidence: str = ""


@dataclass
class Overview:
    rows: list = field(default_factory=list)
    sites: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    @property
    def findings(self) -> list:
        """Only what a person would act on — not the silent levels."""
        return [r for r in self.rows if r.level in (CLEAR, SUSPECTED, UNRESOLVED)]


def collect(run_paths, rules=None) -> Overview:
    rules = rules or load_rules()
    overview = Overview()

    for path in run_paths:
        run = load_run(path)
        overview.warnings.extend(f"{run.target}: {w}" for w in run.warnings)
        findings = [assess(rule, run.table) for rule in rules]

        overview.sites.append({
            "target": run.target,
            "industry": run.industry,
            "timestamp": run.meta.get("timestamp", ""),
            "run_id": run.run_id,
            "counts": {level: sum(1 for f in findings if f.level == level)
                       for level in LEVEL_ORDER},
        })

        for finding in findings:
            overview.rows.append(Row(
                target=run.target or "—",
                industry=run.industry,
                timestamp=run.meta.get("timestamp", ""),
                run_id=run.run_id,
                rule_id=finding.rule.id,
                rule_name=finding.rule.name,
                category=CATEGORY_LABEL.get(finding.rule.category,
                                            finding.rule.category),
                norm=finding.rule.norm,
                level=finding.level,
                status=finding.rule.status,
                condition=finding.condition or "",
                evidence=", ".join(sorted(
                    {e["evidence"] for e in finding.evidence if e.get("evidence")})),
            ))

    return overview


def statistics(overview: Overview) -> dict:
    """Counts by industry, category and provision — over findings only.

    "unauffaellig" and "nicht anwendbar" are deliberately left out of the
    breakdowns: a market observation is about what stands out. They stay
    visible in the per-site totals, so nobody can mistake the base.
    """
    findings = overview.findings
    return {
        "by_industry": _tally(findings, lambda r: r.industry),
        "by_category": _tally(findings, lambda r: r.category),
        "by_norm": _tally(findings, lambda r: r.norm),
        "by_level": [{"key": LEVEL_LABEL[level],
                      "code": level,
                      "count": sum(1 for r in overview.rows if r.level == level)}
                     for level in LEVEL_ORDER
                     if any(r.level == level for r in overview.rows)],
    }


def _tally(rows, key) -> list:
    counts: dict = {}
    for row in rows:
        counts[key(row)] = counts.get(key(row), 0) + 1
    return [{"key": k, "count": n}
            for k, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def build(overview: Overview, output: str | Path = "out",
          as_pdf: bool = False, selection: dict | None = None) -> dict:
    """Write the overview as HTML, CSV and — on request — as a PDF.

    `selection` maps filter name to value (branche / kategorie / stufe /
    norm). The PDF is printed with those filters applied, so the document
    shows exactly the view somebody chose. The agency asked for a
    "Tabelle (z. B. PDF) mit Filtermoeglichkeit"; a PDF that always shows
    everything would answer only half of that.
    """
    folder = Path(output) / "marktuebersicht"
    folder.mkdir(parents=True, exist_ok=True)

    stats = statistics(overview)
    html = _environment().get_template("marktuebersicht.html").render(
        produkt=PRODUCT_NAME,
        zeilen=overview.rows,
        seiten=overview.sites,
        statistik=stats,
        stufen=[{"code": level, "label": LEVEL_LABEL[level]}
                for level in LEVEL_ORDER],
        branchen=sorted({r.industry for r in overview.rows}),
        kategorien=sorted({r.category for r in overview.rows}),
        anzahl_befunde=len(overview.findings),
        warnungen=overview.warnings,
        stufe_label=LEVEL_LABEL,
    )

    html_path = folder / "marktuebersicht.html"
    html_path.write_text(html, encoding="utf-8")

    csv_path = folder / "marktuebersicht.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in overview.rows:
            writer.writerow(asdict(row))

    pdf = render_pdf(html_path, before=apply_filters(selection or {}),
                     landscape=True) if as_pdf else None

    return {"html": html_path, "csv": csv_path, "pdf": pdf,
            "sites": len(overview.sites), "findings": len(overview.findings)}
