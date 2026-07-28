"""Command-line interface for GOaudit."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

from . import __version__
from .core import audit_annotations, summarize
from .data import Taxonomy, default_data_dir, ensure_data, load_constraints, load_groupings, load_ontology, update_data
from .io import convert_eggnog, convert_interpro, read_annotations
from .orgdb import prepare_orgdb_inputs
from .report import write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="goaudit", description="Taxonomic quality control for GO annotations")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate a two-column annotation TSV")
    validate.add_argument("annotations", type=Path, nargs="+", help="one or more two-column annotation TSVs")
    validate.add_argument("--taxid", type=int, required=True, help="target organism NCBI Taxonomy ID")
    validate.add_argument("--output-dir", type=Path, required=True, help="new directory for reports")
    validate.add_argument("--data-dir", type=Path, default=default_data_dir(), help="reference-data directory")
    validate.add_argument("--mode", choices=("report", "flag", "remove"), default="report")
    validate.add_argument("--fail-on-violation", action="store_true", help="exit with status 2 when taxon violations are found")
    validate.add_argument("--force", action="store_true", help="replace an existing output directory")

    update = subparsers.add_parser("update", help="download current GO and NCBI reference data")
    update.add_argument("--data-dir", type=Path, default=default_data_dir())

    convert = subparsers.add_parser("convert-eggnog", help="convert eggNOG-mapper annotations to GOaudit TSV")
    convert.add_argument("input", type=Path)
    convert.add_argument("output", type=Path)
    convert.add_argument("--id-mode", choices=("last-pipe", "full"), default="last-pipe")

    convert_ipr = subparsers.add_parser("convert-interpro", help="convert InterProScan TSV to GOaudit TSV")
    convert_ipr.add_argument("input", type=Path)
    convert_ipr.add_argument("output", type=Path)
    convert_ipr.add_argument("--id-mode", choices=("last-pipe", "full"), default="last-pipe")

    orgdb = subparsers.add_parser("prepare-orgdb", help="prepare validated AnnotationForge tables")
    orgdb.add_argument("audit", type=Path, help="audit.tsv produced by 'goaudit validate'")
    orgdb.add_argument("--gff", type=Path, required=True, help="EGAPx/RefSeq-style GFF3")
    orgdb.add_argument("--output-dir", type=Path, required=True)
    orgdb.add_argument("--min-mapping-coverage", type=float, default=1.0)
    orgdb.add_argument("--force", action="store_true", help="replace an existing output directory")
    return parser


def _validate(args: argparse.Namespace) -> int:
    ensure_data(args.data_dir)
    if args.output_dir.exists():
        if not args.force:
            raise FileExistsError(f"Output directory already exists: {args.output_dir} (use --force to replace it)")
        shutil.rmtree(args.output_dir)
    annotations = [record for path in args.annotations for record in read_annotations(path)]
    ontology = load_ontology(args.data_dir / "go.obo")
    constraints = load_constraints(args.data_dir / "go-computed-taxon-constraints.obo")
    groups = load_groupings(args.data_dir / "go-taxon-groupings.obo")
    taxonomy = Taxonomy(args.data_dir)
    lineage = taxonomy.lineage(args.taxid)
    constraint_taxids = {
        int(value.split(":", 1)[1])
        for mapping in (constraints.in_taxon, constraints.never_in_taxon)
        for values in mapping.values()
        for value in values
        if value.startswith("NCBITaxon:")
    }
    names = taxonomy.names(set(lineage) | constraint_taxids)
    canonical_taxid = taxonomy.canonical(args.taxid)
    records = audit_annotations(annotations, ontology, constraints, lineage, groups, names)
    summary = summarize(records, canonical_taxid, names.get(canonical_taxid, ""), ontology.data_version)
    write_reports(args.output_dir, records, summary, args.mode)
    manifest_path = args.data_dir / "manifest.json"
    if manifest_path.is_file():
        shutil.copyfile(manifest_path, args.output_dir / "reference_manifest.json")
    print(f"GOaudit assessed {summary['annotation_rows']:,} rows across {summary['proteins_annotated']:,} proteins.")
    print(f"Taxon-constraint violations: {summary['taxon_violation_rows']:,} rows ({summary['taxon_violation_terms']:,} unique GO terms).")
    print(f"Report: {args.output_dir / 'summary.tsv'}")
    return 2 if args.fail_on_violation and summary["taxon_violation_rows"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "update":
            manifest = update_data(args.data_dir)
            print(f"Reference data updated in {args.data_dir} at {manifest['updated_at']}")
            return 0
        if args.command == "convert-eggnog":
            counts = convert_eggnog(args.input, args.output, args.id_mode)
            print(f"Wrote {counts['annotations']:,} annotations for {counts['proteins']:,} proteins to {args.output}")
            return 0
        if args.command == "convert-interpro":
            counts = convert_interpro(args.input, args.output, args.id_mode)
            print(
                f"Wrote {counts['annotations']:,} annotations for "
                f"{counts['proteins']:,} proteins to {args.output}"
            )
            return 0
        if args.command == "prepare-orgdb":
            if args.output_dir.exists():
                if not args.force:
                    raise FileExistsError(
                        f"Output directory already exists: {args.output_dir} (use --force to replace it)"
                    )
                shutil.rmtree(args.output_dir)
            summary = prepare_orgdb_inputs(
                args.audit, args.gff, args.output_dir, args.min_mapping_coverage
            )
            print(
                f"Mapped {summary['mapped_proteins']:,}/{summary['retained_proteins']:,} "
                f"proteins ({summary['mapping_coverage']:.2%})."
            )
            print(
                f"Wrote {summary['orgdb_gene_go_rows']:,} gene-GO rows to "
                f"{args.output_dir / 'go.tsv'}"
            )
            return 0
        return _validate(args)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"goaudit: error: {error}\n")


if __name__ == "__main__":
    sys.exit(main())
