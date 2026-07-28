#!/usr/bin/env python3
"""Prepare matched GOaudit and mapping-QC inputs from an NCBI RefSeq release.

The RefSeq GO annotation file is gene-centred, whereas the accompanying FASTA
contains protein accessions.  This script keeps the gene-level associations as
the primary benchmark input and separately checks the GeneID-to-protein mapping
through the RefSeq GFF3.  Protein-expanded associations are emitted for
workflows that explicitly require protein identifiers.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import gzip
import hashlib
import json
from pathlib import Path
import re
from typing import TextIO
from urllib.parse import unquote


GO_PATTERN = re.compile(r"^GO:\d{7}$")


def open_text(path: Path) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_attributes(text: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for item in text.rstrip().split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        attributes[key] = unquote(value)
    return attributes


def gene_ids(attributes: dict[str, str]) -> set[str]:
    values = set()
    for dbxref in attributes.get("Dbxref", "").split(","):
        if dbxref.startswith("GeneID:"):
            values.add(dbxref.split(":", 1)[1])
    return values


def load_fasta_ids(path: Path) -> set[str]:
    identifiers: set[str] = set()
    with open_text(path) as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.startswith(">"):
                continue
            identifier = raw[1:].split(None, 1)[0]
            if not identifier:
                raise ValueError(f"{path}:{line_number}: empty FASTA identifier")
            if identifier in identifiers:
                raise ValueError(f"{path}:{line_number}: duplicate FASTA identifier {identifier}")
            identifiers.add(identifier)
    if not identifiers:
        raise ValueError(f"{path}: no FASTA records found")
    return identifiers


def load_gff_mappings(path: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], int]:
    gene_to_proteins: dict[str, set[str]] = defaultdict(set)
    protein_to_genes: dict[str, set[str]] = defaultdict(set)
    cds_rows = 0
    with open_text(path) as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip() or raw.startswith("#"):
                continue
            fields = raw.rstrip("\n").split("\t")
            if len(fields) != 9:
                raise ValueError(f"{path}:{line_number}: expected 9 GFF3 columns")
            if fields[2] != "CDS":
                continue
            cds_rows += 1
            attributes = parse_attributes(fields[8])
            protein_id = attributes.get("protein_id", "")
            genes = gene_ids(attributes)
            if not protein_id or len(genes) != 1:
                raise ValueError(
                    f"{path}:{line_number}: CDS requires one protein_id and one GeneID Dbxref"
                )
            gene_id = next(iter(genes))
            gene_to_proteins[gene_id].add(protein_id)
            protein_to_genes[protein_id].add(gene_id)
    ambiguous = {protein: genes for protein, genes in protein_to_genes.items() if len(genes) != 1}
    if ambiguous:
        preview = "; ".join(
            f"{protein} -> {sorted(genes)}" for protein, genes in list(ambiguous.items())[:10]
        )
        raise ValueError(f"GFF3 proteins map to multiple GeneIDs: {preview}")
    if not gene_to_proteins:
        raise ValueError(f"{path}: no CDS GeneID-to-protein mappings found")
    return dict(gene_to_proteins), dict(protein_to_genes), cds_rows


def load_gaf(
    path: Path, taxid: int
) -> tuple[set[tuple[str, str]], dict[str, object], dict[str, str]]:
    pairs: set[tuple[str, str]] = set()
    evidence = Counter()
    aspects = Counter()
    qualifiers = Counter()
    metadata: dict[str, str] = {}
    rows = 0
    excluded_not = 0
    wrong_taxon = 0
    with open_text(path) as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.rstrip("\n")
            if line.startswith("!"):
                if ":" in line[1:]:
                    key, value = line[1:].split(":", 1)
                    metadata[key.strip()] = value.strip()
                continue
            if not line:
                continue
            fields = line.split("\t")
            if len(fields) != 17:
                raise ValueError(f"{path}:{line_number}: expected 17 GAF 2.x columns")
            rows += 1
            gene_id, qualifier, go_id = fields[1], fields[3], fields[4]
            if not gene_id:
                raise ValueError(f"{path}:{line_number}: empty DB Object ID")
            if not GO_PATTERN.fullmatch(go_id):
                raise ValueError(f"{path}:{line_number}: invalid GO identifier {go_id!r}")
            row_taxa = {
                value.split(":", 1)[1]
                for value in fields[12].split("|")
                if value.startswith("taxon:")
            }
            if str(taxid) not in row_taxa:
                wrong_taxon += 1
                continue
            qualifier_values = {value for value in qualifier.split("|") if value}
            qualifiers.update(qualifier_values or {"(empty)"})
            if "NOT" in qualifier_values:
                excluded_not += 1
                continue
            evidence[fields[6]] += 1
            aspects[fields[8]] += 1
            pairs.add((gene_id, go_id))
    if not pairs:
        raise ValueError(f"{path}: no positive GO associations for taxid {taxid}")
    summary: dict[str, object] = {
        "gaf_rows": rows,
        "gaf_rows_wrong_taxon": wrong_taxon,
        "gaf_rows_negated": excluded_not,
        "unique_gene_go_associations": len(pairs),
        "annotated_genes": len({gene for gene, _ in pairs}),
        "unique_go_terms": len({go_id for _, go_id in pairs}),
        "evidence_counts": dict(sorted(evidence.items())),
        "aspect_counts": dict(sorted(aspects.items())),
        "qualifier_counts": dict(sorted(qualifiers.items())),
    }
    return pairs, summary, metadata


def write_pairs(path: Path, pairs: set[tuple[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("protein_id", "go_id"))
        writer.writerows(sorted(pairs))


def write_mapping(path: Path, gene_to_proteins: dict[str, set[str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("gene_id", "protein_id"))
        for gene_id in sorted(gene_to_proteins):
            for protein_id in sorted(gene_to_proteins[gene_id]):
                writer.writerow((gene_id, protein_id))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gaf", type=Path, required=True)
    parser.add_argument("--gff", type=Path, required=True)
    parser.add_argument("--proteins", type=Path, required=True)
    parser.add_argument("--taxid", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    fasta_ids = load_fasta_ids(args.proteins)
    gene_to_proteins, protein_to_genes, cds_rows = load_gff_mappings(args.gff)
    gene_pairs, gaf_summary, gaf_metadata = load_gaf(args.gaf, args.taxid)

    gff_proteins = set(protein_to_genes)
    annotated_genes = {gene for gene, _ in gene_pairs}
    mapped_annotated_genes = annotated_genes & set(gene_to_proteins)
    missing_annotated_genes = annotated_genes - set(gene_to_proteins)
    protein_pairs = {
        (protein, go_id)
        for gene, go_id in gene_pairs
        for protein in gene_to_proteins.get(gene, set())
    }
    annotated_proteins = {protein for protein, _ in protein_pairs}

    write_pairs(args.output_dir / "refseq_gene_go.tsv", gene_pairs)
    write_pairs(args.output_dir / "refseq_protein_go.tsv", protein_pairs)
    write_mapping(args.output_dir / "gene_to_protein.tsv", gene_to_proteins)
    (args.output_dir / "unmapped_annotated_genes.txt").write_text(
        "".join(f"{gene}\n" for gene in sorted(missing_annotated_genes)), encoding="utf-8"
    )

    source_paths = (args.gaf, args.gff, args.proteins)
    summary = {
        "taxid": args.taxid,
        "source_files": {
            path.name: {"path": str(path.resolve()), "sha256": sha256(path)} for path in source_paths
        },
        "gaf_metadata": gaf_metadata,
        **gaf_summary,
        "fasta_proteins": len(fasta_ids),
        "gff_cds_rows": cds_rows,
        "gff_proteins": len(gff_proteins),
        "gff_genes_with_protein": len(gene_to_proteins),
        "fasta_gff_proteins_shared": len(fasta_ids & gff_proteins),
        "fasta_proteins_missing_from_gff": len(fasta_ids - gff_proteins),
        "gff_proteins_missing_from_fasta": len(gff_proteins - fasta_ids),
        "annotated_genes_mapped_to_protein": len(mapped_annotated_genes),
        "annotated_genes_without_protein_mapping": len(missing_annotated_genes),
        "gene_mapping_coverage": round(len(mapped_annotated_genes) / len(annotated_genes), 8),
        "protein_expanded_associations": len(protein_pairs),
        "annotated_proteins": len(annotated_proteins),
        "annotated_fasta_proteins": len(annotated_proteins & fasta_ids),
        "genes_with_multiple_proteins": sum(
            len(proteins) > 1 for proteins in gene_to_proteins.values()
        ),
        "sentinel_go_0035070_present": any(go_id == "GO:0035070" for _, go_id in gene_pairs),
    }
    (args.output_dir / "input_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
