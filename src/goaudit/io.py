"""Strict two-column annotation I/O and eggNOG conversion."""

from __future__ import annotations

import csv
from pathlib import Path
import re


GO_PATTERN = re.compile(r"^GO:\d{7}$")
HEADER = ("protein_id", "go_id")


def read_annotations(path: Path) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for line_number, row in enumerate(reader, 1):
            if not row or (len(row) == 1 and not row[0].strip()) or row[0].startswith("#"):
                continue
            if line_number == 1 and tuple(x.strip().lower() for x in row) == HEADER:
                continue
            if len(row) != 2:
                raise ValueError(
                    f"{path}:{line_number}: expected exactly 2 tab-separated columns; found {len(row)}"
                )
            protein, go_id = (value.strip() for value in row)
            if not protein:
                raise ValueError(f"{path}:{line_number}: protein ID is empty")
            if not GO_PATTERN.fullmatch(go_id):
                raise ValueError(
                    f"{path}:{line_number}: invalid GO ID {go_id!r}; expected GO: followed by 7 digits"
                )
            records.append((protein, go_id))
    if not records:
        raise ValueError(f"{path}: no annotation records found")
    return records


def write_annotations(path: Path, records: list[tuple[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(HEADER)
        writer.writerows(records)


def convert_eggnog(input_path: Path, output_path: Path, id_mode: str = "last-pipe") -> dict[str, int]:
    columns: list[str] | None = None
    emitted: list[tuple[str, str]] = []
    proteins_seen = set()
    with input_path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.rstrip("\n")
            if line.startswith("#query\t"):
                columns = line[1:].split("\t")
                continue
            if not line or line.startswith("#"):
                continue
            if columns is None:
                raise ValueError(f"{input_path}:{line_number}: missing eggNOG '#query' header")
            fields = line.split("\t")
            if len(fields) != len(columns):
                raise ValueError(f"{input_path}:{line_number}: row does not match eggNOG header")
            row = dict(zip(columns, fields))
            protein = row["query"]
            if id_mode == "last-pipe":
                protein = protein.rsplit("|", 1)[-1]
            proteins_seen.add(protein)
            seen_terms = set()
            for go_id in row.get("GOs", "-").split(","):
                go_id = go_id.strip()
                if go_id in ("", "-") or go_id in seen_terms:
                    continue
                if not GO_PATTERN.fullmatch(go_id):
                    raise ValueError(f"{input_path}:{line_number}: invalid eggNOG GO ID {go_id!r}")
                emitted.append((protein, go_id))
                seen_terms.add(go_id)
    write_annotations(output_path, emitted)
    return {"proteins": len(proteins_seen), "annotations": len(emitted)}


def convert_interpro(input_path: Path, output_path: Path, id_mode: str = "last-pipe") -> dict[str, int]:
    """Convert InterProScan TSV output, expanding column 14 GO terms."""
    proteins_seen: set[str] = set()
    annotations: set[tuple[str, str]] = set()
    with input_path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip() or raw.startswith("#"):
                continue
            fields = raw.rstrip("\n").split("\t")
            if len(fields) < 14:
                raise ValueError(
                    f"{input_path}:{line_number}: expected at least 14 InterProScan TSV columns"
                )
            protein = fields[0].strip()
            if id_mode == "last-pipe":
                protein = protein.rsplit("|", 1)[-1]
            proteins_seen.add(protein)
            for value in fields[13].split("|"):
                match = re.search(r"GO:\d{7}", value)
                if match:
                    annotations.add((protein, match.group(0)))
    emitted = sorted(annotations)
    write_annotations(output_path, emitted)
    return {"proteins": len(proteins_seen), "annotations": len(emitted)}
