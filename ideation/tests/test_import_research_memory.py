import fcntl
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from ideation.hypothesis_memory import HypothesisMemory

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/import_research_memory.py"
SPEC = importlib.util.spec_from_file_location("import_research_memory", SCRIPT)
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)


class ImportMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.runs = self.root / "retained-runs"
        self.runs.mkdir()
        original = HypothesisMemory(self.root / "original.sqlite")
        self.card = {"id": "H1", "mechanism": "Remove redundant work", "proposed_change": "Fuse", "parents": []}
        self.run = "/home/ubuntu/AutoResearch-Inference/ideation/runs/example"
        self.identity = original.register(self.run, self.card, {"baseline": {"image": "sha256:known"}}, {"criteria": []})
        original.review(self.identity, {"status": "deferred", "reasons": ["Timing missing"]}, {"result": "defer"})
        self.test = original.plan_test(self.identity, {"request_id": "recovery-test", "task": "measure"}, {"hardware": "H200"})
        record = original.get(self.identity)
        original.db.close()
        self.export = {"stats": {"hypotheses": 10, "events": 30, "tests": 3}, "scope": "one retained record", "hypotheses": [record]}
        self.export_path = self.runs / "memory-export.json"
        self.export_path.write_text(json.dumps(self.export))

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_collection_preserves_partial_coverage_without_state_write(self):
        bundle = IMPORTER.collect([self.runs])
        report = IMPORTER.summary(bundle)
        self.assertEqual(report["recoverable_hypotheses"], 1)
        self.assertEqual(report["export_coverage"][0]["available_in_this_export"], {"hypotheses": 1, "events": 3, "tests": 1})
        self.assertEqual(report["export_coverage"][0]["not_in_this_export"]["hypotheses"], 9)
        self.assertEqual(bundle["records"][0]["id"], self.identity)
        self.assertFalse((self.root / "state").exists())

    def test_apply_idempotence_keeps_original_id_and_plans_not_outcomes(self):
        bundle = IMPORTER.collect([self.runs])
        state = self.root / "state"
        first = IMPORTER.apply(bundle, state)
        second = IMPORTER.apply(bundle, state)
        self.assertEqual(first["inserted"], 1)
        self.assertEqual(first["planned_tests_restored"], 1)
        self.assertEqual(second["inserted"], 0)
        self.assertEqual(second["existing"], 1)
        self.assertEqual(second["planned_tests_restored"], 0)
        self.assertEqual(first["ledger_stats"], second["ledger_stats"])
        ledger = HypothesisMemory(state / "research/hypotheses.sqlite")
        record = ledger.get(self.identity)
        self.assertEqual(record["run"], self.run)
        self.assertEqual(record["status"], "deferred")
        self.assertEqual(record["tests"][0]["id"], self.test["id"])
        self.assertEqual(record["tests"][0]["status"], "planned")
        self.assertFalse(record["tests"][0]["results"])
        raw = ledger.db.execute("SELECT data FROM nodes WHERE kind='legacy_hypothesis_snapshot'").fetchone()[0]
        self.assertEqual(json.loads(raw)["events"], self.export["hypotheses"][0]["events"])
        ledger.db.close()

    def test_known_history_identity_is_resolved_against_original_root(self):
        self.export_path.unlink()
        folder = self.runs / "example"
        folder.mkdir()
        (folder / "history.json").write_text(json.dumps([{"card": self.card, "global_id": self.identity}]))
        record = IMPORTER.collect([self.runs])["records"][0]
        self.assertEqual(record["id"], self.identity)
        self.assertEqual(record["run"], self.run)

    def test_unknown_original_hash_is_not_replaced_with_local_path_id(self):
        self.export_path.unlink()
        (self.runs / "history.json").write_text(json.dumps([{"card": self.card, "global_id": "hypothesis:unknown"}]))
        bundle = IMPORTER.collect([self.runs])
        self.assertFalse(bundle["records"])
        self.assertEqual(len(bundle["artifacts"]), 1)
        self.assertIn("not regenerated", bundle["gaps"][0]["reason"])

    def test_active_writer_blocks_import(self):
        state = self.root / "state"
        state.mkdir()
        with (state / ".writer.lock").open("a+b") as writer:
            fcntl.flock(writer, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(RuntimeError, "active writer"):
                IMPORTER.apply(IMPORTER.collect([self.runs]), state)
        self.assertFalse((state / "research/hypotheses.sqlite").exists())


if __name__ == "__main__":
    unittest.main()
