from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONVERTER = ROOT / "benchmarks" / "stylophora_deepgoplus" / "convert_deepgoplus.py"
MERGER = ROOT / "benchmarks" / "stylophora_deepgoplus" / "merge_audit_scores.py"


class DeepGOPlusBenchmarkTests(unittest.TestCase):
    def test_conversion_keeps_maximum_score_and_unannotated_proteins(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            raw = directory / "raw.tsv"
            scored = directory / "scored.tsv"
            goaudit = directory / "goaudit.tsv"
            raw.write_text(
                "p1\tGO:0000001|0.400\tGO:0000001|0.600\tGO:0000002|0.300\n"
                "p2\n"
            )

            result = subprocess.run(
                [sys.executable, str(CONVERTER), str(raw), str(scored), str(goaudit)],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(
                scored.read_text(),
                "protein_id\tgo_id\tscore\n"
                "p1\tGO:0000001\t0.600\n"
                "p1\tGO:0000002\t0.300\n",
            )
            self.assertIn("proteins_without_predictions\t1", result.stdout)

    def test_score_merger_selects_only_taxon_violations(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            scored = directory / "scored.tsv"
            audit = directory / "audit.tsv"
            output = directory / "violations.tsv"
            scored.write_text(
                "protein_id\tgo_id\tscore\np1\tGO:0000001\t0.700\np1\tGO:0000002\t0.400\n"
            )
            audit.write_text(
                "protein_id\toriginal_go_id\tgo_id\tterm_name\tnamespace\tstatus\t"
                "constraint_type\tconstraint_taxon\tconstraint_taxon_name\tmessage\n"
                "p1\tGO:0000001\tGO:0000001\tbad term\tbiological_process\t"
                "taxon_violation\tin_taxon\tNCBITaxon:1\tTest taxon\tincompatible\n"
                "p1\tGO:0000002\tGO:0000002\tgood term\tbiological_process\t"
                "valid\t\t\t\t\n"
            )

            subprocess.run(
                [sys.executable, str(MERGER), str(scored), str(audit), str(output)],
                check=True,
                capture_output=True,
                text=True,
            )

            rows = output.read_text().splitlines()
            self.assertEqual(len(rows), 2)
            self.assertIn("p1\tGO:0000001\t0.700\tbad term", rows[1])


if __name__ == "__main__":
    unittest.main()
