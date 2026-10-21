import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("historical_import", REPO / "scripts/import_recovered_experiments.py")
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class RecoveredImportTests(unittest.TestCase):
    def test_retained_receipts_map_exactly_without_service_claim(self):
        items = IMPORTER.records(REPO / "ideation/runs/h200-overnight-001")
        self.assertEqual([(x["scope"], x["status"]) for x in items],
                         [("component", "validated"), ("component", "inconclusive"), ("native", "error")])
        self.assertTrue(all(x["original_event_id"].startswith("event:") for x in items))

    def test_checksum_tampering_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            source = REPO / "ideation/runs/h200-overnight-001"
            target = Path(directory)
            (target / "evaluator").mkdir()
            for filename in ("memory-component-and-short-results.json", "memory-native-003-result.json"):
                shutil.copyfile(source / filename, target / filename)
            for name in ("C25_COMPONENT_RESULT_REVIEW.md", "C24_SHORT_PROBE_RESULT_REVIEW.md", "C25_NATIVE_003_INTERRUPTION_REVIEW.md"):
                shutil.copyfile(source / "evaluator" / name, target / "evaluator" / name)
            (target / "evaluator/C25_COMPONENT_RESULT_REVIEW.md").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "checksum"):
                IMPORTER.records(target)


if __name__ == "__main__":
    unittest.main()
