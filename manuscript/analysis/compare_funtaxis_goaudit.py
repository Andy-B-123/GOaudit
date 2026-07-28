#!/usr/bin/env python3
"""Diagnostic comparison of a FunTaxIS-lite taxon list and a GOaudit run.

This is a landscape-analysis helper, not a performance benchmark. A valid
same-release comparison requires regenerating the FunTaxIS-lite list from the
same GO, GOA and NCBI Taxonomy snapshots used for GOaudit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from goaudit.core import audit_annotations
from goaudit.data import Taxonomy, load_constraints, load_groupings, load_ontology


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--funtaxis-list", required=True, type=Path)
    parser.add_argument("--taxid", required=True, type=int)
    parser.add_argument("--output", type=Path, help="optional JSON output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ontology = load_ontology(args.data_dir / "go.obo")
    constraints = load_constraints(
        args.data_dir / "go-computed-taxon-constraints.obo"
    )
    groupings = load_groupings(args.data_dir / "go-taxon-groupings.obo")
    taxonomy = Taxonomy(args.data_dir)

    official_results = audit_annotations(
        [("term", go_id) for go_id in ontology.terms],
        ontology,
        constraints,
        taxonomy.lineage(args.taxid),
        groupings,
        {},
    )
    official = {
        result.go_id
        for result in official_results
        if result.status == "taxon_violation"
    }

    funtaxis_status: Counter[str] = Counter()
    funtaxis: set[str] = set()
    with args.funtaxis_list.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            supplied_id = line.split("\t", 1)[0]
            canonical_id, term = ontology.resolve(supplied_id)
            if term is None:
                funtaxis_status["unknown"] += 1
            elif term.obsolete:
                funtaxis_status["obsolete"] += 1
            else:
                funtaxis_status[
                    "alternate" if canonical_id != supplied_id else "current"
                ] += 1
                funtaxis.add(canonical_id)

    association_counts: Counter[tuple[bool, bool]] = Counter()
    skipped_statuses: Counter[str] = Counter()
    with args.audit.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["status"] in {"obsolete", "unknown_go_term"}:
                skipped_statuses[row["status"]] += 1
                continue
            association_counts[
                (row["status"] == "taxon_violation", row["go_id"] in funtaxis)
            ] += 1

    intersection = official & funtaxis
    union = official | funtaxis
    result = {
        "warning": (
            "Diagnostic only: release and policy differences are confounded unless "
            "the FunTaxIS-lite list is regenerated from matched references."
        ),
        "inputs": {
            "taxid": args.taxid,
            "funtaxis_list": str(args.funtaxis_list),
            "funtaxis_list_sha256": sha256(args.funtaxis_list),
            "goaudit_audit": str(args.audit),
            "goaudit_audit_sha256": sha256(args.audit),
            "data_dir": str(args.data_dir),
        },
        "funtaxis_identifier_status": dict(sorted(funtaxis_status.items())),
        "term_sets": {
            "goaudit_official": len(official),
            "funtaxis_current_canonical": len(funtaxis),
            "both": len(intersection),
            "goaudit_only": len(official - funtaxis),
            "funtaxis_only": len(funtaxis - official),
            "jaccard": len(intersection) / len(union) if union else 1.0,
        },
        "associations": {
            "neither": association_counts[(False, False)],
            "funtaxis_only": association_counts[(False, True)],
            "both": association_counts[(True, True)],
            "goaudit_only": association_counts[(True, False)],
            "comparable": sum(association_counts.values()),
            "skipped": dict(sorted(skipped_statuses.items())),
        },
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
