#!/usr/bin/env python3
"""Link GOaudit decisions back to evidence fields in the source RefSeq GAF."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import json
from pathlib import Path
import re
from typing import TextIO


FLAGGED = frozenset(("taxon_violation", "obsolete", "unknown_go_term"))


def open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def source_databases(with_from: str) -> set[str]:
    databases = set()
    for value in re.split(r"[|,]", with_from):
        value = value.strip()
        if value:
            databases.add(value.split(":", 1)[0])
    return databases or {"(empty)"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gaf", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    decisions: dict[tuple[str, str], dict[str, str]] = {}
    audit_statuses = Counter()
    term_counts = Counter()
    constraint_counts = Counter()
    with args.audit.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {
            "protein_id",
            "original_go_id",
            "go_id",
            "term_name",
            "status",
            "constraint_type",
            "constraint_taxon",
            "constraint_taxon_name",
            "message",
        }
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Audit is missing columns: {', '.join(sorted(missing))}")
        for row in reader:
            key = (row["protein_id"], row["original_go_id"])
            if key in decisions:
                raise ValueError(f"Audit contains duplicate association {key}")
            decisions[key] = row
            audit_statuses[row["status"]] += 1
            if row["status"] == "taxon_violation":
                term_counts[(row["go_id"], row["term_name"])] += 1
                constraint_counts[
                    (
                        row["constraint_type"],
                        row["constraint_taxon"],
                        row["constraint_taxon_name"],
                    )
                ] += 1

    columns = (
        "gene_id",
        "original_go_id",
        "current_go_id",
        "term_name",
        "status",
        "constraint_type",
        "constraint_taxon",
        "constraint_taxon_name",
        "qualifier",
        "reference",
        "evidence_code",
        "with_from",
        "aspect",
        "assigned_by",
        "annotation_date",
        "message",
    )
    source_statuses = Counter()
    all_databases = Counter()
    database_statuses: dict[str, Counter[str]] = defaultdict(Counter)
    violation_databases = Counter()
    violation_evidence = Counter()
    matched_pairs: set[tuple[str, str]] = set()
    output_path = args.output_dir / "flagged_gaf_rows.tsv"
    with output_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        with open_text(args.gaf) as handle:
            for line_number, raw in enumerate(handle, 1):
                if not raw.strip() or raw.startswith("!"):
                    continue
                fields = raw.rstrip("\n").split("\t")
                if len(fields) != 17:
                    raise ValueError(f"{args.gaf}:{line_number}: expected 17 GAF columns")
                key = (fields[1], fields[4])
                decision = decisions.get(key)
                if decision is None:
                    continue
                status = decision["status"]
                source_statuses[status] += 1
                matched_pairs.add(key)
                databases = source_databases(fields[7])
                all_databases.update(databases)
                for database in databases:
                    database_statuses[database][status] += 1
                if status not in FLAGGED:
                    continue
                if status == "taxon_violation":
                    violation_evidence[fields[6]] += 1
                    violation_databases.update(databases)
                writer.writerow(
                    {
                        "gene_id": fields[1],
                        "original_go_id": fields[4],
                        "current_go_id": decision["go_id"],
                        "term_name": decision["term_name"],
                        "status": status,
                        "constraint_type": decision["constraint_type"],
                        "constraint_taxon": decision["constraint_taxon"],
                        "constraint_taxon_name": decision["constraint_taxon_name"],
                        "qualifier": fields[3],
                        "reference": fields[5],
                        "evidence_code": fields[6],
                        "with_from": fields[7],
                        "aspect": fields[8],
                        "assigned_by": fields[14],
                        "annotation_date": fields[13],
                        "message": decision["message"],
                    }
                )

    unmatched = set(decisions) - matched_pairs
    summary = {
        "audit_association_status_counts": dict(sorted(audit_statuses.items())),
        "gaf_source_row_status_counts": dict(sorted(source_statuses.items())),
        "gaf_source_database_counts": dict(sorted(all_databases.items())),
        "gaf_source_database_status_counts": {
            database: dict(sorted(counts.items()))
            for database, counts in sorted(database_statuses.items())
        },
        "matched_unique_associations": len(matched_pairs),
        "unmatched_unique_associations": len(unmatched),
        "taxon_violation_source_database_counts": dict(sorted(violation_databases.items())),
        "taxon_violation_source_evidence_counts": dict(sorted(violation_evidence.items())),
        "taxon_violation_terms": [
            {"go_id": go_id, "term_name": name, "associations": count}
            for (go_id, name), count in sorted(
                term_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        "taxon_violation_constraints": [
            {
                "constraint_type": constraint_type,
                "constraint_taxon": taxon,
                "constraint_taxon_name": name,
                "associations": count,
            }
            for (constraint_type, taxon, name), count in sorted(
                constraint_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ],
    }
    (args.output_dir / "source_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
