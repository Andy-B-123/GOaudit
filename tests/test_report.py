from pathlib import Path
import tempfile
import unittest

from goaudit.core import AuditRecord
from goaudit.io import read_annotations
from goaudit.report import write_reports


class ReportTests(unittest.TestCase):
    def test_remove_mode_only_removes_taxon_violations(self):
        records = [
            AuditRecord("p1", "GO:0000001", "GO:0000001", "ok", "biological_process", "valid"),
            AuditRecord("p1", "GO:0035070", "GO:0035070", "bad", "biological_process", "taxon_violation"),
            AuditRecord("p2", "GO:0000002", "GO:0000002", "old", "molecular_function", "obsolete"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            write_reports(output, records, {"annotation_rows": 3}, "remove")
            self.assertEqual(
                read_annotations(output / "annotations_filtered.tsv"),
                [("p1", "GO:0000001"), ("p2", "GO:0000002")],
            )
            for name in ("audit.tsv", "summary.json", "summary.tsv", "status_counts.svg", "namespace_counts.svg", "top_taxon_violations.svg"):
                self.assertTrue((output / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
