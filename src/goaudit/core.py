"""GO taxon-constraint validation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .data import Constraints, Ontology


@dataclass(frozen=True)
class AuditRecord:
    protein_id: str
    original_go_id: str
    go_id: str
    term_name: str
    namespace: str
    status: str
    constraint_type: str = ""
    constraint_taxon: str = ""
    constraint_taxon_name: str = ""
    message: str = ""


def _taxon_number(identifier: str) -> int | None:
    if identifier.startswith("NCBITaxon:"):
        return int(identifier.split(":", 1)[1])
    return None


def audit_annotations(
    annotations: list[tuple[str, str]],
    ontology: Ontology,
    constraints: Constraints,
    lineage: tuple[int, ...],
    grouping_members: dict[str, tuple[int, ...]],
    taxon_names: dict[int, str],
) -> list[AuditRecord]:
    lineage_set = set(lineage)

    def matches(identifier: str) -> bool:
        number = _taxon_number(identifier)
        if number is not None:
            return number in lineage_set
        return any(member in lineage_set for member in grouping_members.get(identifier, ()))

    def display_name(identifier: str) -> str:
        number = _taxon_number(identifier)
        return taxon_names.get(number, "") if number is not None else "taxon union"

    result: list[AuditRecord] = []
    for protein, original_id in annotations:
        go_id, term = ontology.resolve(original_id)
        if term is None:
            result.append(AuditRecord(protein, original_id, go_id, "", "unknown", "unknown_go_term", message="GO ID is absent from the ontology release"))
            continue
        common = (protein, original_id, go_id, term.name, term.namespace)
        if term.obsolete:
            replacement = ", ".join(term.replaced_by) or "no replacement supplied"
            result.append(AuditRecord(*common, "obsolete", message=f"Obsolete GO term; {replacement}"))
            continue
        never = next((taxon for taxon in constraints.never_in_taxon.get(go_id, ()) if matches(taxon)), None)
        if never:
            result.append(AuditRecord(*common, "taxon_violation", "never_in_taxon", never, display_name(never), f"Term must never be used for {display_name(never) or never} or its descendants"))
            continue
        failed_only = next((taxon for taxon in constraints.in_taxon.get(go_id, ()) if not matches(taxon)), None)
        if failed_only:
            result.append(AuditRecord(*common, "taxon_violation", "in_taxon", failed_only, display_name(failed_only), f"Term is restricted to {display_name(failed_only) or failed_only} or its descendants"))
            continue
        status = "alternate_id" if original_id != go_id else "valid"
        message = f"Resolved alternate ID to {go_id}" if status == "alternate_id" else ""
        result.append(AuditRecord(*common, status, message=message))
    return result


def summarize(records: list[AuditRecord], target_taxid: int, target_name: str, ontology_version: str) -> dict:
    status_counts = Counter(record.status for record in records)
    proteins = {record.protein_id for record in records}
    violating_proteins = {record.protein_id for record in records if record.status == "taxon_violation"}
    unique_terms = {record.go_id for record in records}
    unique_violations = {record.go_id for record in records if record.status == "taxon_violation"}
    unique_obsolete = {record.go_id for record in records if record.status == "obsolete"}
    unique_unknown = {record.go_id for record in records if record.status == "unknown_go_term"}
    return {
        "target_taxid": target_taxid,
        "target_name": target_name,
        "ontology_version": ontology_version,
        "proteins_annotated": len(proteins),
        "annotation_rows": len(records),
        "unique_go_terms": len(unique_terms),
        "valid_rows": status_counts["valid"] + status_counts["alternate_id"],
        "taxon_violation_rows": status_counts["taxon_violation"],
        "taxon_violation_terms": len(unique_violations),
        "proteins_with_taxon_violations": len(violating_proteins),
        "obsolete_rows": status_counts["obsolete"],
        "obsolete_terms": len(unique_obsolete),
        "unknown_go_rows": status_counts["unknown_go_term"],
        "unknown_go_terms": len(unique_unknown),
        "alternate_id_rows": status_counts["alternate_id"],
        "rows_recommended_for_taxon_exclusion": status_counts["taxon_violation"],
    }
