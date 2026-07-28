#!/usr/bin/env python3
"""Convert DeepGOPlus scored output into long and GOaudit TSV files."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


GO_ID = re.compile(r"GO:\d{7}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="DeepGOPlus raw prediction TSV")
    parser.add_argument("scored_output", type=Path, help="three-column scored TSV")
    parser.add_argument("goaudit_output", type=Path, help="two-column GOaudit TSV")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    predictions: dict[tuple[str, str], float] = {}
    proteins = set()

    with args.input.open() as handle:
        for line_number, line in enumerate(handle, 1):
            fields = line.rstrip("\n").split("\t")
            protein_id = fields[0].strip()
            if not protein_id:
                raise ValueError(f"line {line_number}: empty protein identifier")
            proteins.add(protein_id)
            for value in fields[1:]:
                try:
                    go_id, score_text = value.rsplit("|", 1)
                    score = float(score_text)
                except ValueError as error:
                    raise ValueError(
                        f"line {line_number}: invalid prediction {value!r}"
                    ) from error
                if not GO_ID.fullmatch(go_id):
                    raise ValueError(f"line {line_number}: invalid GO ID {go_id!r}")
                if not 0.0 <= score <= 1.0:
                    raise ValueError(f"line {line_number}: invalid score {score}")
                key = (protein_id, go_id)
                predictions[key] = max(score, predictions.get(key, 0.0))

    ordered = sorted(
        ((protein_id, go_id, score) for (protein_id, go_id), score in predictions.items()),
        key=lambda row: (row[0], row[1]),
    )
    with args.scored_output.open("w") as scored, args.goaudit_output.open("w") as goaudit:
        scored.write("protein_id\tgo_id\tscore\n")
        goaudit.write("protein_id\tgo_id\n")
        for protein_id, go_id, score in ordered:
            scored.write(f"{protein_id}\t{go_id}\t{score:.3f}\n")
            goaudit.write(f"{protein_id}\t{go_id}\n")

    annotated = {protein_id for protein_id, _, _ in ordered}
    print(f"input_proteins\t{len(proteins)}")
    print(f"annotated_proteins\t{len(annotated)}")
    print(f"proteins_without_predictions\t{len(proteins - annotated)}")
    print(f"protein_go_associations\t{len(ordered)}")
    print(f"unique_go_terms\t{len({go_id for _, go_id, _ in ordered})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
