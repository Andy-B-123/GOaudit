from pathlib import Path
import tempfile
import unittest

from goaudit.io import convert_eggnog, convert_interpro, read_annotations


class IOTests(unittest.TestCase):
    def test_reads_header_and_strict_two_columns(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.tsv"
            path.write_text("protein_id\tgo_id\np1\tGO:0000001\n")
            self.assertEqual(read_annotations(path), [("p1", "GO:0000001")])
            path.write_text("p1\tGO:0000001\textra\n")
            with self.assertRaisesRegex(ValueError, "exactly 2"):
                read_annotations(path)

    def test_rejects_comma_separated_go_terms(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.tsv"
            path.write_text("p1\tGO:0000001,GO:0000002\n")
            with self.assertRaisesRegex(ValueError, "invalid GO ID"):
                read_annotations(path)

    def test_converts_eggnog_and_trims_pipe_prefix(self):
        content = """## emapper-2.1.12
#query\tseed_ortholog\tGOs
gnl|WGS:ZZZZ|egapxtmp_003494-P1\thit\tGO:0035070,GO:0000002
p2\thit\t-
"""
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "eggnog.tsv"
            output = Path(temporary) / "annotations.tsv"
            source.write_text(content)
            counts = convert_eggnog(source, output)
            self.assertEqual(counts, {"proteins": 2, "annotations": 2})
            self.assertEqual(
                read_annotations(output),
                [("egapxtmp_003494-P1", "GO:0035070"), ("egapxtmp_003494-P1", "GO:0000002")],
            )

    def test_converts_and_deduplicates_interpro_go_terms(self):
        row = [
            "gnl|WGS:TEST|p1", "md5", "100", "Pfam", "PF1", "desc", "1", "20",
            "1e-5", "T", "2026-01-01", "IPR1", "domain", "GO:0000001(InterPro)|GO:0000002", "-",
        ]
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "interpro.tsv"
            output = Path(temporary) / "annotations.tsv"
            source.write_text("\t".join(row) + "\n" + "\t".join(row) + "\n")
            counts = convert_interpro(source, output)
            self.assertEqual(counts, {"proteins": 1, "annotations": 2})
            self.assertEqual(
                read_annotations(output),
                [("p1", "GO:0000001"), ("p1", "GO:0000002")],
            )


if __name__ == "__main__":
    unittest.main()
