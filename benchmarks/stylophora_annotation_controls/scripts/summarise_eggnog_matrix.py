#!/usr/bin/env python3
"""Collate the eggNOG-mapper option matrix into one table.

Reads the GOaudit summary written for every cell of
`run_eggnog_option_matrix.slurm` and emits a TSV describing, for each option
set, how much of the proteome was annotated and how much of the result was
formally incompatible with the target lineage.

Usage:
    python summarise_eggnog_matrix.py [matrix_dir] [output.tsv]
"""

from __future__ import annotations

import sys
from pathlib import Path

DEFAULT_MATRIX = Path(
    "/scratch3/bac050/2026_bioinfo_tool/results/comparator_benchmark/eggnog_matrix"
)
INPUT_PROTEINS = 32879

# cell directory -> (search stage, human-readable annotation policy)
CELLS = [
    ("default_search_default_annot", "defaults", "emapper defaults (tax_scope auto, non-electronic)"),
    ("default_search_all_evidence", "defaults", "defaults + --go_evidence all"),
    ("metazoa_scope", "defaults", "--tax_scope Metazoa, donors unrestricted, all evidence"),
    ("nonbilaterian_donors", "defaults", "donors Metazoa minus Bilateria, all evidence"),
    ("cnidaria_donors_all", "defaults", "donors Cnidaria, all evidence"),
    ("cnidaria_donors_nonelectronic", "defaults", "donors Cnidaria, non-electronic"),
    ("stringent_search_default_annot", "stringent", "emapper default annotation policy"),
    ("stringent_search_nonbilaterian", "stringent", "donors Metazoa minus Bilateria, all evidence"),
]

FIELDS = [
    "proteins_annotated",
    "annotation_rows",
    "unique_go_terms",
    "valid_rows",
    "taxon_violation_rows",
    "taxon_violation_terms",
    "proteins_with_taxon_violations",
    "obsolete_rows",
    "obsolete_terms",
]


def read_summary(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    with path.open(encoding="utf-8") as handle:
        next(handle, None)
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 2:
                values[parts[0]] = parts[1]
    return values


def pct(numerator: float, denominator: float) -> str:
    if not denominator:
        return "0.000"
    return f"{100 * numerator / denominator:.3f}"


def main() -> int:
    matrix = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_MATRIX
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else matrix / "option_matrix_summary.tsv"

    header = [
        "cell",
        "search",
        "annotation_policy",
        "proteins_annotated",
        "proteome_coverage_pct",
        "annotation_rows",
        "unique_go_terms",
        "valid_rows",
        "taxon_violation_rows",
        "taxon_violation_pct",
        "taxon_violation_terms",
        "proteins_with_taxon_violations",
        "obsolete_rows",
        "obsolete_pct",
        "obsolete_terms",
    ]
    rows = [header]

    for cell, search, policy in CELLS:
        summary_path = matrix / cell / "goaudit" / "summary.tsv"
        if not summary_path.exists():
            print(f"missing: {summary_path}", file=sys.stderr)
            continue
        values = read_summary(summary_path)
        proteins = int(values.get("proteins_annotated", 0))
        rows_total = int(values.get("annotation_rows", 0))
        violations = int(values.get("taxon_violation_rows", 0))
        obsolete = int(values.get("obsolete_rows", 0))
        rows.append([
            cell,
            search,
            policy,
            str(proteins),
            pct(proteins, INPUT_PROTEINS),
            str(rows_total),
            values.get("unique_go_terms", "0"),
            values.get("valid_rows", "0"),
            str(violations),
            pct(violations, rows_total),
            values.get("taxon_violation_terms", "0"),
            values.get("proteins_with_taxon_violations", "0"),
            str(obsolete),
            pct(obsolete, rows_total),
            values.get("obsolete_terms", "0"),
        ])

    out.write_text("\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8")
    widths = [max(len(r[i]) for r in rows) for i in range(len(header))]
    show = [0, 3, 4, 5, 6, 8, 9, 12]
    for r in rows:
        print("  ".join(r[i].ljust(widths[i]) for i in show))
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
