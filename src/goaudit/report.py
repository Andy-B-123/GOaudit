"""Write machine-readable audit reports and lightweight SVG plots."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import csv
import html
import json
from pathlib import Path

from .core import AuditRecord
from .io import write_annotations


def write_audit(path: Path, records: list[AuditRecord]) -> None:
    fields = list(asdict(records[0]).keys()) if records else list(AuditRecord.__dataclass_fields__)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)


def _bar_chart(path: Path, title: str, counts: list[tuple[str, int]], colour: str = "#277da1") -> None:
    width = 900
    row_height = 42
    top = 80
    left = 250
    height = max(180, top + row_height * len(counts) + 45)
    maximum = max((value for _, value in counts), default=1) or 1
    plot_width = width - left - 100
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="30" y="42" font-family="sans-serif" font-size="24" font-weight="bold">{html.escape(title)}</text>',
    ]
    for index, (label, value) in enumerate(counts):
        y = top + index * row_height
        bar_width = value / maximum * plot_width
        elements.extend([
            f'<text x="{left - 12}" y="{y + 20}" text-anchor="end" font-family="sans-serif" font-size="15">{html.escape(label)}</text>',
            f'<rect x="{left}" y="{y}" width="{bar_width:.1f}" height="26" rx="3" fill="{colour}"/>',
            f'<text x="{left + bar_width + 8:.1f}" y="{y + 20}" font-family="sans-serif" font-size="15">{value}</text>',
        ])
    elements.append("</svg>")
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def write_reports(output_dir: Path, records: list[AuditRecord], summary: dict, mode: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_audit(output_dir / "audit.tsv", records)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "summary.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("metric", "value"))
        writer.writerows(summary.items())

    if mode == "flag":
        write_audit(output_dir / "annotations_flagged.tsv", records)
    elif mode == "remove":
        kept = [(record.protein_id, record.go_id) for record in records if record.status != "taxon_violation"]
        write_annotations(output_dir / "annotations_filtered.tsv", kept)

    status = Counter(record.status for record in records)
    _bar_chart(output_dir / "status_counts.svg", "Annotation QC status", sorted(status.items()), "#277da1")
    namespaces = Counter(record.namespace for record in records)
    _bar_chart(output_dir / "namespace_counts.svg", "GO namespace", sorted(namespaces.items()), "#43aa8b")
    violations = Counter(f"{record.go_id} {record.term_name}" for record in records if record.status == "taxon_violation")
    _bar_chart(output_dir / "top_taxon_violations.svg", "Most frequent taxon violations", violations.most_common(10), "#f94144")
