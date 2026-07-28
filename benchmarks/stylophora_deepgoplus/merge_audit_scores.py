#!/usr/bin/env python3
"""Attach DeepGOPlus confidence scores to GOaudit taxon violations."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("scored_predictions", type=Path)
    parser.add_argument("audit", type=Path)
    parser.add_argument("output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.scored_predictions.open() as handle:
        scores = {
            (row["protein_id"], row["go_id"]): row["score"]
            for row in csv.DictReader(handle, delimiter="\t")
        }

    fields = [
        "protein_id",
        "go_id",
        "score",
        "term_name",
        "namespace",
        "constraint_type",
        "constraint_taxon",
        "constraint_taxon_name",
        "message",
    ]
    violations = []
    with args.audit.open() as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["status"] != "taxon_violation":
                continue
            row["score"] = scores[(row["protein_id"], row["original_go_id"])]
            violations.append(row)

    violations.sort(key=lambda row: (-float(row["score"]), row["go_id"], row["protein_id"]))
    with args.output.open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in violations)

    print(f"taxon_violation_rows\t{len(violations)}")
    print(f"taxon_violation_terms\t{len({row['go_id'] for row in violations})}")
    print(f"affected_proteins\t{len({row['protein_id'] for row in violations})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
