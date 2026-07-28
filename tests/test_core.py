from pathlib import Path
import tempfile
import unittest

from goaudit.core import audit_annotations, summarize
from goaudit.data import Taxonomy, load_constraints, load_groupings, load_ontology


ONTOLOGY = """format-version: 1.2
data-version: releases/2026-07-01

[Term]
id: GO:0035070
name: salivary gland histolysis
namespace: biological_process
alt_id: GO:1234567

[Term]
id: GO:0000001
name: old term
namespace: biological_process
is_obsolete: true
replaced_by: GO:0000002

[Term]
id: GO:0000002
name: valid term
namespace: molecular_function
"""

CONSTRAINTS = """format-version: 1.2

[Term]
id: GO:0035070
relationship: RO:0002162 NCBITaxon:6656

[Term]
id: GO:0000002
property_value: RO:0002161 NCBITaxon:999
"""

GROUPINGS = """format-version: 1.2

[Term]
id: NCBITaxon_Union:0000001
union_of: NCBITaxon:6656
union_of: NCBITaxon:33090
"""


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        directory = Path(self.temporary.name)
        (directory / "go.obo").write_text(ONTOLOGY)
        (directory / "constraints.obo").write_text(CONSTRAINTS)
        (directory / "groups.obo").write_text(GROUPINGS)
        self.ontology = load_ontology(directory / "go.obo")
        self.constraints = load_constraints(directory / "constraints.obo")
        self.groups = load_groupings(directory / "groups.obo")

    def tearDown(self):
        self.temporary.cleanup()

    def test_coral_salivary_gland_term_is_violation(self):
        records = audit_annotations(
            [("egapxtmp_003494-P1", "GO:0035070")],
            self.ontology,
            self.constraints,
            lineage=(50429, 6073, 33208, 2759, 1),
            grouping_members=self.groups,
            taxon_names={6656: "Arthropoda"},
        )
        self.assertEqual(records[0].status, "taxon_violation")
        self.assertEqual(records[0].constraint_type, "in_taxon")
        self.assertIn("Arthropoda", records[0].message)

    def test_arthropod_term_is_valid_for_descendant(self):
        records = audit_annotations(
            [("fly", "GO:0035070")], self.ontology, self.constraints,
            lineage=(7227, 7215, 6656, 1), grouping_members=self.groups,
            taxon_names={6656: "Arthropoda"},
        )
        self.assertEqual(records[0].status, "valid")

    def test_obsolete_unknown_and_alternate_ids(self):
        records = audit_annotations(
            [("p1", "GO:0000001"), ("p2", "GO:9999999"), ("p3", "GO:1234567")],
            self.ontology, self.constraints, lineage=(1,), grouping_members=self.groups,
            taxon_names={},
        )
        self.assertEqual([record.status for record in records], ["obsolete", "unknown_go_term", "taxon_violation"])
        self.assertEqual(records[2].go_id, "GO:0035070")

    def test_summary_counts_rows_proteins_and_terms(self):
        records = audit_annotations(
            [("p1", "GO:0000002"), ("p1", "GO:0035070")],
            self.ontology, self.constraints, lineage=(50429, 1,), grouping_members=self.groups,
            taxon_names={6656: "Arthropoda"},
        )
        summary = summarize(records, 50429, "Stylophora pistillata", self.ontology.data_version)
        self.assertEqual(summary["proteins_annotated"], 1)
        self.assertEqual(summary["annotation_rows"], 2)
        self.assertEqual(summary["unique_go_terms"], 2)
        self.assertEqual(summary["taxon_violation_rows"], 1)
        self.assertEqual(summary["obsolete_terms"], 0)

    def test_taxonomy_reads_ncbi_delimiters_and_merged_ids(self):
        directory = Path(self.temporary.name)
        (directory / "nodes.dmp").write_text(
            "1\t|\t1\t|\tno rank\t|\n10\t|\t1\t|\tspecies\t|\n"
        )
        (directory / "merged.dmp").write_text("9\t|\t10\t|\n")
        (directory / "names.dmp").write_text(
            "1\t|\troot\t|\t\t|\tscientific name\t|\n"
            "10\t|\tTest species\t|\t\t|\tscientific name\t|\n"
        )
        taxonomy = Taxonomy(directory)
        self.assertEqual(taxonomy.lineage(9), (10, 1))
        self.assertEqual(taxonomy.names({10}), {10: "Test species"})


if __name__ == "__main__":
    unittest.main()
