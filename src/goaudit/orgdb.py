"""Prepare validated AnnotationForge inputs from a GOaudit audit and GFF3."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
import json
from pathlib import Path
from urllib.parse import unquote


RETAINED_STATUSES = frozenset(("valid", "alternate_id"))
AUDIT_COLUMNS = frozenset(("protein_id", "go_id", "status"))


@dataclass(frozen=True)
class Gene:
    feature_id: str
    gid: str
    symbol: str
    name: str
    chromosome: str


@dataclass(frozen=True)
class ProteinMapping:
    query_protein_id: str
    gff_protein_id: str
    transcript_id: str
    gid: str
    match_method: str


@dataclass
class GFFIndex:
    genes: dict[str, Gene]
    mappings: dict[str, tuple[str, str]]
    canonical_mappings: dict[str, tuple[str, str, str]]
    summary: dict[str, int]

    def map_protein(self, protein_id: str) -> ProteinMapping | None:
        if protein_id in self.mappings:
            gid, transcript = self.mappings[protein_id]
            return ProteinMapping(protein_id, protein_id, transcript, gid, "exact")
        canonical = canonical_protein_id(protein_id)
        hit = self.canonical_mappings.get(canonical)
        if hit is None:
            return None
        gff_protein, gid, transcript = hit
        return ProteinMapping(protein_id, gff_protein, transcript, gid, "canonical_last_pipe")


def canonical_protein_id(protein_id: str) -> str:
    """Apply GOaudit's single documented protein-ID normalization."""
    return protein_id.rsplit("|", 1)[-1]


def parse_gff_attributes(text: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for item in text.rstrip().split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        attributes[key] = unquote(value)
    return attributes


def load_egapx_gff(path: Path) -> GFFIndex:
    """Load the required gene -> transcript -> CDS/protein hierarchy."""
    genes_raw: dict[str, Gene] = {}
    gids: dict[str, str] = {}
    transcript_parents: dict[str, set[str]] = defaultdict(set)
    protein_transcripts: dict[str, set[str]] = defaultdict(set)
    feature_counts: Counter[str] = Counter()
    errors: list[str] = []

    with path.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            if not raw.strip() or raw.startswith("#"):
                continue
            fields = raw.rstrip("\n").split("\t")
            if len(fields) != 9:
                errors.append(f"line {line_number}: expected 9 GFF3 columns")
                continue
            chromosome, _, feature_type, _, _, _, _, _, attribute_text = fields
            feature_counts[feature_type] += 1
            attributes = parse_gff_attributes(attribute_text)

            if feature_type == "gene":
                feature_id = attributes.get("ID", "")
                gid = attributes.get("locus_tag", "")
                if not feature_id or not gid:
                    errors.append(f"line {line_number}: gene requires ID and locus_tag")
                    continue
                symbol = attributes.get("gene") or attributes.get("Name") or gid
                name = attributes.get("description") or attributes.get("product") or symbol
                gene = Gene(feature_id, gid, symbol, name, chromosome)
                if feature_id in genes_raw and genes_raw[feature_id] != gene:
                    errors.append(f"line {line_number}: conflicting gene ID {feature_id}")
                if gid in gids and gids[gid] != feature_id:
                    errors.append(f"line {line_number}: locus_tag {gid} belongs to multiple genes")
                genes_raw[feature_id] = gene
                gids[gid] = feature_id

            elif feature_type in ("mRNA", "transcript"):
                transcript_id = attributes.get("ID", "")
                parents = [value.strip() for value in attributes.get("Parent", "").split(",") if value.strip()]
                if not transcript_id or not parents:
                    errors.append(f"line {line_number}: {feature_type} requires ID and Parent")
                    continue
                transcript_parents[transcript_id].update(parents)

            elif feature_type == "CDS":
                protein_id = attributes.get("protein_id", "")
                parents = [value.strip() for value in attributes.get("Parent", "").split(",") if value.strip()]
                if not protein_id or not parents:
                    errors.append(f"line {line_number}: CDS requires protein_id and Parent")
                    continue
                protein_transcripts[protein_id].update(parents)

    if errors:
        preview = "\n".join(errors[:20])
        suffix = f"\n... and {len(errors) - 20} more" if len(errors) > 20 else ""
        raise ValueError(f"GFF3 does not satisfy the EGAPx/RefSeq schema:\n{preview}{suffix}")
    if not genes_raw or not transcript_parents or not protein_transcripts:
        raise ValueError("GFF3 must contain gene, transcript/mRNA, and CDS features")

    resolved: dict[str, tuple[str, str]] = {}
    resolution_errors: list[str] = []
    for protein_id, transcripts in protein_transcripts.items():
        gene_hits: set[tuple[str, str]] = set()
        for transcript_id in transcripts:
            parents = transcript_parents.get(transcript_id)
            if not parents:
                resolution_errors.append(f"protein {protein_id}: missing transcript {transcript_id}")
                continue
            if len(parents) != 1:
                resolution_errors.append(f"transcript {transcript_id}: expected one gene Parent, found {len(parents)}")
                continue
            gene_feature_id = next(iter(parents))
            gene = genes_raw.get(gene_feature_id)
            if gene is None:
                resolution_errors.append(f"transcript {transcript_id}: missing gene {gene_feature_id}")
                continue
            gene_hits.add((gene.gid, transcript_id))
        gids_for_protein = {gid for gid, _ in gene_hits}
        if len(gids_for_protein) != 1:
            resolution_errors.append(f"protein {protein_id}: maps to {len(gids_for_protein)} genes")
            continue
        if len(gene_hits) != 1:
            resolution_errors.append(f"protein {protein_id}: maps to multiple transcripts")
            continue
        resolved[protein_id] = next(iter(gene_hits))

    canonical_candidates: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for protein_id, (gid, transcript) in resolved.items():
        canonical_candidates[canonical_protein_id(protein_id)].append((protein_id, gid, transcript))
    collisions = {key: hits for key, hits in canonical_candidates.items() if len(hits) != 1}
    if collisions:
        examples = "; ".join(f"{key}: {hits}" for key, hits in list(collisions.items())[:10])
        resolution_errors.append(f"canonical protein-ID collisions: {examples}")
    if resolution_errors:
        preview = "\n".join(resolution_errors[:20])
        suffix = f"\n... and {len(resolution_errors) - 20} more" if len(resolution_errors) > 20 else ""
        raise ValueError(f"Ambiguous or broken GFF3 hierarchy:\n{preview}{suffix}")

    canonical = {key: hits[0] for key, hits in canonical_candidates.items()}
    summary = {
        "gff_gene_features": len(genes_raw),
        "gff_transcripts": len(transcript_parents),
        "gff_proteins": len(resolved),
        "gff_cds_rows": feature_counts["CDS"],
    }
    return GFFIndex(genes_raw, resolved, canonical, summary)


def _write_table(path: Path, fieldnames: tuple[str, ...], rows) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def prepare_orgdb_inputs(
    audit_path: Path,
    gff_path: Path,
    output_dir: Path,
    min_mapping_coverage: float = 1.0,
) -> dict:
    """Write validated gene_info, chromosome, GO, and mapping-QC tables."""
    if not 0 <= min_mapping_coverage <= 1:
        raise ValueError("min_mapping_coverage must be between 0 and 1")
    gff = load_egapx_gff(gff_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    retained: list[tuple[str, str]] = []
    proteins: set[str] = set()
    status_counts: Counter[str] = Counter()
    with audit_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = AUDIT_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Audit TSV is missing columns: {', '.join(sorted(missing))}")
        for line_number, row in enumerate(reader, 2):
            status = row["status"]
            status_counts[status] += 1
            if status not in RETAINED_STATUSES:
                continue
            protein_id, go_id = row["protein_id"], row["go_id"]
            if not protein_id or not go_id:
                raise ValueError(f"{audit_path}:{line_number}: empty protein_id or go_id")
            proteins.add(protein_id)
            retained.append((protein_id, go_id))

    mappings: dict[str, ProteinMapping] = {}
    unmapped: list[str] = []
    for protein_id in sorted(proteins):
        mapping = gff.map_protein(protein_id)
        if mapping is None:
            unmapped.append(protein_id)
        else:
            mappings[protein_id] = mapping
    coverage = len(mappings) / len(proteins) if proteins else 0.0

    _write_table(
        output_dir / "protein_to_gene.tsv",
        ("query_protein_id", "gff_protein_id", "transcript_id", "GID", "match_method"),
        (
            {
                "query_protein_id": value.query_protein_id,
                "gff_protein_id": value.gff_protein_id,
                "transcript_id": value.transcript_id,
                "GID": value.gid,
                "match_method": value.match_method,
            }
            for value in sorted(mappings.values(), key=lambda item: item.query_protein_id)
        ),
    )
    _write_table(
        output_dir / "unmapped_proteins.tsv",
        ("protein_id",),
        ({"protein_id": protein_id} for protein_id in unmapped),
    )

    gene_go = sorted({(mappings[protein].gid, go_id) for protein, go_id in retained if protein in mappings})
    genes = sorted(gff.genes.values(), key=lambda gene: gene.gid)
    _write_table(
        output_dir / "gene_info.tsv",
        ("GID", "SYMBOL", "GENENAME"),
        ({"GID": gene.gid, "SYMBOL": gene.symbol, "GENENAME": gene.name} for gene in genes),
    )
    _write_table(
        output_dir / "chromosome.tsv",
        ("GID", "CHROMOSOME"),
        ({"GID": gene.gid, "CHROMOSOME": gene.chromosome} for gene in genes),
    )
    _write_table(
        output_dir / "go.tsv",
        ("GID", "GO", "EVIDENCE"),
        ({"GID": gid, "GO": go_id, "EVIDENCE": "IEA"} for gid, go_id in gene_go),
    )

    summary: dict[str, object] = {
        **gff.summary,
        "audit_rows": sum(status_counts.values()),
        "retained_audit_rows": len(retained),
        "retained_proteins": len(proteins),
        "mapped_proteins": len(mappings),
        "unmapped_proteins": len(unmapped),
        "mapping_coverage": round(coverage, 8),
        "minimum_mapping_coverage": min_mapping_coverage,
        "orgdb_gene_rows": len(genes),
        "orgdb_gene_go_rows": len(gene_go),
        "orgdb_genes_with_go": len({gid for gid, _ in gene_go}),
        "orgdb_unique_go_terms": len({go_id for _, go_id in gene_go}),
        "audit_status_counts": dict(sorted(status_counts.items())),
    }
    (output_dir / "mapping_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with (output_dir / "mapping_summary.tsv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("metric", "value"))
        for key, value in summary.items():
            writer.writerow((key, json.dumps(value, sort_keys=True) if isinstance(value, dict) else value))

    if not proteins:
        raise ValueError("Audit has no valid or alternate-ID annotations to include in an OrgDb")
    if coverage < min_mapping_coverage:
        raise ValueError(
            f"Protein-to-gene mapping coverage {coverage:.2%} is below the required "
            f"{min_mapping_coverage:.2%}; see {output_dir / 'unmapped_proteins.tsv'}"
        )
    return summary
