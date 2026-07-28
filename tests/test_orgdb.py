import csv
import json
from pathlib import Path
import tempfile
import unittest

from goaudit.orgdb import load_egapx_gff, prepare_orgdb_inputs


GFF = """##gff-version 3
scaffold1\tGnomon\tgene\t1\t100\t.\t+\t.\tID=gene-g1;Name=gene_one;locus_tag=g1;description=Example%20gene
scaffold1\tGnomon\tmRNA\t1\t100\t.\t+\t.\tID=rna-g1-R1;Parent=gene-g1
scaffold1\tGnomon\tCDS\t1\t40\t.\t+\t0\tID=cds-g1-P1;Parent=rna-g1-R1;protein_id=gnl|WGS:TEST|g1-P1
scaffold1\tGnomon\tCDS\t60\t100\t.\t+\t0\tID=cds-g1-P1;Parent=rna-g1-R1;protein_id=gnl|WGS:TEST|g1-P1
"""

AUDIT = """protein_id\toriginal_go_id\tgo_id\tterm_name\tnamespace\tstatus\tconstraint_type\tconstraint_taxon\tconstraint_taxon_name\tmessage
g1-P1\tGO:0000001\tGO:0000001\tvalid\tbiological_process\tvalid\t\t\t\t
g1-P1\tGO:0000002\tGO:0000002\tbad\tbiological_process\ttaxon_violation\tin_taxon\tNCBITaxon:6656\tArthropoda\tbad
g1-P1\tGO:0000003\tGO:0000003\told\tbiological_process\tobsolete\t\t\t\told
"""


class OrgDbTests(unittest.TestCase):
    def test_loads_hierarchy_and_maps_canonical_identifier(self):
        with tempfile.TemporaryDirectory() as temporary:
            gff = Path(temporary) / "test.gff"
            gff.write_text(GFF)
            index = load_egapx_gff(gff)
            mapping = index.map_protein("g1-P1")
            self.assertIsNotNone(mapping)
            self.assertEqual(mapping.gid, "g1")
            self.assertEqual(mapping.transcript_id, "rna-g1-R1")
            self.assertEqual(mapping.match_method, "canonical_last_pipe")
            self.assertEqual(index.summary["gff_cds_rows"], 2)

    def test_prepares_annotationforge_tables_from_retained_statuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gff, audit, output = root / "test.gff", root / "audit.tsv", root / "output"
            gff.write_text(GFF)
            audit.write_text(AUDIT)
            summary = prepare_orgdb_inputs(audit, gff, output)
            self.assertEqual(summary["mapping_coverage"], 1.0)
            self.assertEqual(summary["orgdb_gene_go_rows"], 1)
            with (output / "go.tsv").open() as handle:
                rows = list(csv.DictReader(handle, delimiter="\t"))
            self.assertEqual(rows, [{"GID": "g1", "GO": "GO:0000001", "EVIDENCE": "IEA"}])
            mapping_summary = json.loads((output / "mapping_summary.json").read_text())
            self.assertEqual(mapping_summary["audit_status_counts"]["obsolete"], 1)
            self.assertEqual((output / "unmapped_proteins.tsv").read_text(), "protein_id\n")

    def test_fails_below_mapping_threshold_but_keeps_qc(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gff, audit, output = root / "test.gff", root / "audit.tsv", root / "output"
            gff.write_text(GFF)
            audit.write_text(AUDIT.replace("g1-P1", "missing-P1"))
            with self.assertRaisesRegex(ValueError, "below the required"):
                prepare_orgdb_inputs(audit, gff, output)
            self.assertTrue((output / "mapping_summary.tsv").is_file())
            self.assertIn("missing-P1", (output / "unmapped_proteins.tsv").read_text())

    def test_rejects_ambiguous_protein_to_gene_hierarchy(self):
        bad = GFF + """scaffold2\tGnomon\tgene\t1\t100\t.\t+\t.\tID=gene-g2;Name=g2;locus_tag=g2
scaffold2\tGnomon\tmRNA\t1\t100\t.\t+\t.\tID=rna-g2-R1;Parent=gene-g2
scaffold2\tGnomon\tCDS\t1\t100\t.\t+\t0\tID=cds-other;Parent=rna-g2-R1;protein_id=gnl|WGS:TEST|g1-P1
"""
        with tempfile.TemporaryDirectory() as temporary:
            gff = Path(temporary) / "bad.gff"
            gff.write_text(bad)
            with self.assertRaisesRegex(ValueError, "maps to 2 genes"):
                load_egapx_gff(gff)


if __name__ == "__main__":
    unittest.main()
