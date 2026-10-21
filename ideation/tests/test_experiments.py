import concurrent.futures
import hashlib
import json
import sqlite3
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ideation.experiments import ExperimentRegistry


class ExperimentRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.registry = ExperimentRegistry(self.root)
        self.roi = {"metric": "ITL", "unit": "ms", "baseline_value": None,
                    "expected_relative_gain": None, "min_relative_gain": 0.02,
                    "assumptions": ["Component timing may be hidden by overlap"],
                    "unknowns": ["Measure native critical path in a 5 minute pilot"]}
        self.plan = {"workload": "mooncake", "budget_gpu_hours": 1,
                     "measurement": "Compare critical path time; no service claim"}

    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()

    def create(self, identity="C25-component-01", scope="component", **extra):
        return self.registry.create(identity, "hypothesis:existing-memory-id", "baseline:sha256", scope,
                                    provenance={"code_commit": "pinned-commit", "hardware": "H200"},
                                    roi=self.roi, evaluation_plan=self.plan, **extra)

    def start_attempt(self):
        record = self.create()
        for status in ("accepted", "planned", "running"):
            record = self.registry.transition(record["id"], status, note=status)
        return record

    def test_unknown_roi_is_allowed_and_scope_is_not_promoted(self):
        component = self.start_attempt()
        artifact = self.root / "measurements.json"
        artifact.write_text('{"microseconds_saved": 45}')
        self.create("C25-service-01", scope="service")
        record = self.registry.transition(component["id"], "validated", note="Component-only improvement",
                                          artifacts=[artifact], metrics={"microseconds_saved": 45})
        self.assertEqual(record["scope"], "component")
        self.assertEqual(self.registry.get("C25-service-01")["status"], "proposed")
        reference = record["events"][-1]["payload"]["artifacts"][0]
        self.assertEqual(reference["sha256"], hashlib.sha256(artifact.read_bytes()).hexdigest())
        self.assertEqual(reference["verification"], "local_content_hashed")

    def test_idempotent_event_retry_and_conflict(self):
        record = self.create(event_id="create-request")
        self.assertEqual(record, self.create(event_id="create-request"))
        first = self.registry.transition(record["id"], "accepted", note="pass", event_id="review-request")
        self.assertEqual(first, self.registry.transition(record["id"], "accepted", note="pass", event_id="review-request"))
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            self.registry.transition(record["id"], "rejected", note="different", event_id="review-request")
        self.assertEqual(len(self.registry.get(record["id"])["events"]), 2)

    def test_terminal_attempt_cannot_restart_and_artifacts_required(self):
        identity = self.start_attempt()["id"]
        with self.assertRaisesRegex(ValueError, "artifact"):
            self.registry.transition(identity, "validated", note="no evidence")
        self.registry.transition(identity, "error", note="Startup failed before measurements")
        with self.assertRaisesRegex(ValueError, "Invalid transition"):
            self.registry.transition(identity, "running", note="restart")
        self.assertEqual(self.registry.list(status="error")[0]["id"], identity)

    def test_acceptance_requires_explicit_roi_and_plan(self):
        identity = self.registry.create("pilot", "hypothesis:x", "baseline:x", "native", provenance={"source": "x"})["id"]
        with self.assertRaisesRegex(ValueError, "ROI"):
            self.registry.transition(identity, "accepted", note="not ready")
        with self.assertRaisesRegex(ValueError, "unknowns"):
            self.registry.transition(identity, "accepted", note="not ready", roi={**self.roi, "unknowns": []}, evaluation_plan=self.plan)
        record = self.registry.transition(identity, "accepted", note="cheap bounded diagnostic", roi=self.roi, evaluation_plan=self.plan)
        self.assertIsNone(record["roi"]["expected_relative_gain"])
        with self.assertRaisesRegex(ValueError, "Stale"):
            self.registry.transition(identity, "planned", note="stale reader", expected_status="proposed")

    def test_path_injection_and_sql_edits_are_rejected(self):
        for identity in ("../../escape", "/tmp/escape", "x'; DROP TABLE experiments;--", "x\nnew"):
            with self.assertRaises(ValueError):
                self.create(identity)
        record = self.create()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
            self.registry.db.execute("DELETE FROM experiments WHERE id=?", (record["id"],))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
            self.registry.db.execute("UPDATE experiment_events SET status='validated'")
        self.assertEqual(self.registry.get(record["id"])["status"], "proposed")

    def test_concurrent_review_only_one_wins(self):
        identity = self.create()["id"]
        root = self.root
        def review(status):
            registry = ExperimentRegistry(root)
            try:
                return registry.transition(identity, status, note=status, expected_status="proposed")["status"]
            except ValueError:
                return "conflict"
            finally:
                registry.close()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(review, ("accepted", "rejected")))
        self.assertEqual(results.count("conflict"), 1)
        self.assertEqual(len(self.registry.get(identity)["events"]), 2)

    def test_historical_import_preserves_scope_without_fabricated_execution(self):
        artifact = self.root / "retained-receipt.json"
        artifact.write_text('{"original_verdict": "validated"}')
        arguments = dict(experiment_id="recovered-C25", hypothesis_id="hypothesis:old", baseline_id="baseline:old",
                         scope="component", status="validated", provenance={"source_receipt": "retained"},
                         artifacts=[artifact], note="Historical component result only",
                         original_event_id="event:old", original_at="2026-10-20T22:41:04Z")
        record = self.registry.import_historical(**arguments)
        self.assertEqual(record, self.registry.import_historical(**arguments))
        self.assertEqual([event["status"] for event in record["events"]], ["validated"])
        self.assertIsNone(record["roi"])
        self.assertTrue(record["events"][0]["payload"]["historical_import"])
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            self.registry.import_historical(**{**arguments, "scope": "service"})

    def test_retained_evidence_relocates_after_original_source_is_gone(self):
        artifact = self.root / "evidence.json"
        artifact.write_text('{"scope": "component", "saved_us": 45}')
        record = self.registry.import_historical("portable", "hypothesis:old", "baseline:old", "component",
            status="validated", provenance={"source": "retained"}, artifacts=[artifact], note="Component only",
            original_event_id="event:portable", original_at="2026-10-20T22:41:04Z")
        before = [tuple(row) for row in self.registry.db.execute("SELECT * FROM experiment_events")]
        self.assertEqual(record["resolved_artifacts"][0]["retention_status"], "retained_verified")
        self.registry.close()
        relocated = self.root / "replacement-node"
        shutil.copytree(self.root / "experiments", relocated / "experiments")
        artifact.unlink()
        self.registry = ExperimentRegistry(relocated)
        record = self.registry.get("portable")
        reference = record["resolved_artifacts"][0]
        self.assertEqual(reference["retention_status"], "retained_verified")
        self.assertTrue(reference["resolved_local_file"].startswith(str(relocated.resolve())))
        self.assertEqual(json.loads(Path(reference["resolved_local_file"]).read_text())["saved_us"], 45)
        self.assertEqual(before, [tuple(row) for row in self.registry.db.execute("SELECT * FROM experiment_events")])
        Path(reference["resolved_local_file"]).write_text("corrupted")
        self.assertEqual(self.registry.get("portable")["resolved_artifacts"][0]["retention_status"], "retained_copy_hash_mismatch")

    def test_materialize_existing_receipts_without_rewriting_them(self):
        artifact = self.root / "retained.md"
        artifact.write_text("Historical evaluator review")
        with mock.patch.object(self.registry, "retain_artifacts", return_value={}):
            self.registry.import_historical("legacy", "hypothesis:old", "baseline:old", "component",
                status="inconclusive", provenance={"source": "receipt"}, artifacts=[artifact], note="No service conclusion",
                original_event_id="event:legacy", original_at="2026-10-20T22:41:04Z")
        before = [tuple(row) for row in self.registry.db.execute("SELECT * FROM experiment_events")]
        result = self.registry.retain_artifacts()
        self.assertEqual(result["retained_verified"], 1)
        self.assertFalse(result["event_receipts_modified"])
        self.assertEqual(before, [tuple(row) for row in self.registry.db.execute("SELECT * FROM experiment_events")])

    def test_sensitive_binary_and_oversized_artifacts_are_not_copied(self):
        filenames = ("credentials.json", "profile.nsys-rep", "huge.txt")
        expected = ("blocked_sensitive_filename", "unsupported_artifact_type_external_retention_required",
                    "exceeds_16MiB_external_retention_required")
        for index, (filename, status) in enumerate(zip(filenames, expected)):
            artifact = self.root / filename
            artifact.write_bytes(b"private" if index < 2 else b"x" * (16 * 1024 * 1024 + 1))
            record = self.registry.import_historical("excluded-" + str(index), "hypothesis:old", "baseline:old", "component",
                status="inconclusive", provenance={"source": "receipt"}, artifacts=[artifact], note="Recorded externally",
                original_event_id="event:excluded-" + str(index), original_at="2026-10-20T22:41:04Z")
            self.assertEqual(record["resolved_artifacts"][0]["retention_status"], status)
        self.assertEqual(self.registry.db.execute("SELECT COUNT(*) FROM artifact_copies").fetchone()[0], 0)

    def test_export_survives_reopen_and_remote_hash_is_not_attested(self):
        identity = self.start_attempt()["id"]
        self.registry.transition(identity, "validated", note="Operator imported evidence", artifacts=[
            {"uri": "s3://example/evidence.json", "sha256": "a" * 64, "verification": "verified"}])
        target = self.root / "snapshots" / "events.json"
        exported = self.registry.export(target)
        self.assertEqual(exported, json.loads(target.read_text()))
        self.registry.close()
        self.registry = ExperimentRegistry(self.root)
        self.assertEqual(exported, self.registry.export())
        artifact = exported["experiments"][0]["events"][-1]["payload"]["artifacts"][0]
        self.assertEqual(artifact["verification"], "caller_supplied_unverified")


if __name__ == "__main__":
    unittest.main()
