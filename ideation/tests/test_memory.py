import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from ideation.hypothesis_memory import HypothesisMemory


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.memory = HypothesisMemory(self.root / "memory.sqlite")
        self.card = {"id": "H1", "parents": [], "statement": "Reduce TPOT", "mechanism": "Avoid redundant staging",
                     "proposed_change": "Use existing grouped backend", "evidence": [{"source_id": "github:1", "quote": "staging", "relation": "supports"}]}
        self.brief = {"task": "Improve deployment", "baseline": {"commit": "abc"}}
        self.policy = {"require_novelty": False}
        self.scope = {"baseline": "abc", "workload": "decode8k"}
        self.artifact = self.root / "result.json"
        self.artifact.write_text('{"tpot_ms": 7}')

    def tearDown(self):
        self.memory.db.close()
        self.temp.cleanup()

    def register(self, run="run1", card=None):
        return self.memory.register(run, card or self.card, self.brief, self.policy,
                                    [{"id": "github:1", "body": "staging"}])

    def test_registration_survives_crashed_review_and_is_idempotent(self):
        identity = self.register()
        self.assertEqual(identity, self.register())
        self.memory.db.close()
        self.memory = HypothesisMemory(self.root / "memory.sqlite")
        value = self.memory.get(identity)
        self.assertEqual(value["status"], "proposed")
        self.assertEqual(len(value["events"]), 1)
        self.assertEqual(value["card"], self.card)
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            self.register(card={**self.card, "statement": "Silent replacement"})
        self.assertEqual(self.memory.get(identity)["card"], self.card)

    def test_rejection_can_be_revisited_under_new_policy_without_forgetting(self):
        identity = self.register()
        self.memory.review(identity, {"status": "rejected", "reasons": ["Legacy novelty rule"]}, {}, {"require_novelty": True})
        self.memory.review(identity, {"status": "accepted", "eligible": True}, {}, self.policy)
        record = self.memory.get(identity)
        self.assertEqual(record["status"], "accepted")
        self.assertEqual([e["data"]["status"] for e in record["events"] if e["type"] == "reviewed"], ["rejected", "accepted"])
        self.assertEqual(record["experiment_status"], "untested")
        self.assertEqual(len(self.memory.query(status="accepted", baseline="abc", text="TPOT")), 1)

    def test_cross_run_duplicates_are_relations_and_not_rejections(self):
        first = self.register()
        self.memory.review(first, {"eligible": False}, {})
        second = self.register("run2", {**self.card, "parents": [first]})
        graph = self.memory.graph(second)
        self.assertTrue(any(e["relation"] == "same_mechanism_as" and e["dst"] == first for e in graph["edges"]))
        self.assertTrue(any(e["relation"] == "derived_from" and e["dst"] == first for e in graph["edges"]))
        self.assertEqual(self.memory.get(second)["status"], "proposed")
        self.assertTrue(any(n["kind"] == "source" and n["data"].get("body") == "staging" for n in graph["nodes"]))

    def test_experimental_verdict_is_scoped_and_separate_from_selection(self):
        identity = self.register()
        self.memory.review(identity, {"status": "accepted"}, {})
        test = self.memory.plan_test(identity, {"control": "old", "treatment": "new", "request_id": "one"}, self.scope)
        self.assertEqual(test, self.memory.plan_test(identity, test["plan"], self.scope))
        self.memory.start_test(test["id"])
        self.assertEqual(self.memory.get(identity)["tests"][0]["status"], "running")
        self.memory.test_result(test["id"], "invalidated", self.artifact, "No gain on this workload")
        record = self.memory.get(identity)
        self.assertEqual(record["status"], "accepted")
        self.assertEqual(record["experiment_status"], "tested")
        self.assertEqual(record["outcomes_by_scope"][0]["status"], "invalidated")
        self.assertEqual(record["tests"][0]["status"], "completed")
        self.assertEqual(record["outcomes_by_scope"][0]["scope"], self.scope)
        with self.assertRaises(ValueError):
            self.memory.start_test(test["id"])
        self.assertTrue(any(n["kind"] == "artifact" and len(n["data"]["sha256"]) == 64 for n in self.memory.graph(identity)["nodes"]))

    def test_repeat_evidence_conflict_is_not_silently_overwritten(self):
        identity = self.register()
        first = self.memory.plan_test(identity, {"run": 1}, self.scope)
        event = self.memory.test_result(first["id"], "validated", self.artifact, "report")
        self.assertEqual(event, self.memory.test_result(first["id"], "validated", self.artifact, "report"))
        with self.assertRaisesRegex(ValueError, "repeat test"):
            self.memory.test_result(first["id"], "invalidated", self.artifact, "changed mind")
        second = self.memory.plan_test(identity, {"run": 2}, self.scope)
        self.memory.test_result(second["id"], "invalidated", self.artifact, "repeat contradicts")
        self.assertEqual(self.memory.get(identity)["outcomes_by_scope"][0]["status"], "conflicting")
        third = self.memory.plan_test(identity, {"run": 3}, {**self.scope, "workload": "prefill"})
        self.memory.test_result(third["id"], "validated", self.artifact, "different workload")
        self.assertEqual(len(self.memory.get(identity)["outcomes_by_scope"]), 2)

    def test_error_is_not_invalidated_and_artifact_required(self):
        identity = self.register()
        test = self.memory.plan_test(identity, {"run": 1}, self.scope)
        with self.assertRaises(ValueError):
            self.memory.test_result(test["id"], "validated", self.root / "missing", "report")
        self.memory.test_result(test["id"], "error", self.artifact, "OOM")
        self.assertEqual(self.memory.get(identity)["tests"][0]["status"], "error")
        self.assertEqual(self.memory.query(status="invalidated"), [])

    def test_append_only_audit_and_atomic_conflict(self):
        identity = self.register()
        with self.assertRaises(sqlite3.IntegrityError):
            self.memory.db.execute("DELETE FROM events")
        self.memory.db.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            self.memory.db.execute("UPDATE nodes SET data='{}' WHERE id=?", (identity,))
        self.memory.db.rollback()
        with self.assertRaises(ValueError):
            self.memory.review(identity, {"status": "validated"}, {})
        self.assertEqual(self.memory.get(identity)["status"], "proposed")

    def test_history_migration_idempotent_and_preserves_old_policy(self):
        folder = self.root / "runs" / "old" / "hypotheses"
        folder.mkdir(parents=True)
        for name, value in {"history.json": [{"card": self.card, "assessment": {"eligible": False, "reasons": ["novelty"]}, "review": {}}],
                            "brief.json": self.brief, "rubric.json": {"novelty": 15}, "sources.json": []}.items():
            (folder / name).write_text(json.dumps(value))
        result = self.memory.import_runs(self.root / "runs")
        self.assertEqual(result["imported"], 1)
        self.assertEqual(result["errors"], [])
        self.assertEqual(self.memory.import_runs(self.root / "runs")["existing"], 1)
        record = self.memory.get(self.memory.query()[0]["id"])
        self.assertEqual(record["policy"], {"novelty": 15})
        self.assertEqual(record["status"], "rejected")
        self.assertEqual(len(record["events"]), 3)

    def test_unknown_parents_fail_atomically(self):
        with self.assertRaisesRegex(ValueError, "Unknown hypothesis"):
            self.register(card={**self.card, "parents": ["absent"]})
        self.assertEqual(self.memory.stats()["hypotheses"], 0)

    def test_review_context_and_crashed_proposals_are_preserved(self):
        folder = self.root / "runs" / "crashed"
        folder.mkdir(parents=True)
        (folder / "propose-1.json").write_text(json.dumps({"hypotheses": [self.card]}))
        imported = self.memory.import_runs(self.root / "runs")
        self.assertEqual(imported["imported"], 1)
        identity = self.memory.query()[0]["id"]
        self.memory.review(identity, {"status": "deferred"}, {}, context={"prior_art": {"query": "staging"}, "sources": [{"id": "paper:1", "body": "negative evidence"}]})
        context = [n for n in self.memory.graph(identity)["nodes"] if n["kind"] == "review_context"][0]
        self.assertEqual(context["data"]["sources"][0]["body"], "negative evidence")

    def test_legacy_partial_rejections_and_revisions_preserved(self):
        folder = self.root / "runs" / "old"
        folder.mkdir(parents=True)
        (folder / "draft.json").write_text(json.dumps({"hypotheses": [self.card], "rejected_leads": ["No baseline applicability"], "comparators": ["Upstream flag"]}))
        (folder / "final.json").write_text(json.dumps({"hypotheses": [{**self.card, "statement": "Revised"}]}))
        result = self.memory.import_runs(self.root / "runs")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["imported"], 4)
        self.assertEqual(len(self.memory.query(status="rejected")), 1)
        self.assertTrue(self.memory.query(status="rejected")[0]["card"]["legacy_partial_record"])
        self.assertEqual(self.memory.import_runs(self.root / "runs")["existing"], 4)

    def test_recall_ranks_task_baseline_and_preserves_negative_scope(self):
        irrelevant = self.register("other", {**self.card, "mechanism": "Improve network storage", "statement": "Storage caches", "proposed_change": "Files"})
        relevant = self.register("relevant", {**self.card, "mechanism": "Optimize routed GEMM staging on B200", "statement": "Reduce decode TPOT on B200"})
        self.memory.review(relevant, {"status": "rejected", "reasons": ["Measured regression under decode scope"]}, {})
        test = self.memory.plan_test(relevant, {"run": 1}, self.scope)
        self.memory.test_result(test["id"], "invalidated", self.artifact, "Regression")
        result = self.memory.recall({**self.brief, "instructions": "Optimize routed GEMM staging", "target": {"gpu": "B200"}}, limit=1)
        self.assertEqual(result[0]["id"], relevant)
        self.assertTrue(result[0]["recall"]["known_baseline_match"])
        self.assertEqual(result[0]["status"], "rejected")
        self.assertEqual(result[0]["outcomes"][0]["scope"], self.scope)
        self.assertEqual(result[0]["outcomes"][0]["status"], "invalidated")
        self.assertNotEqual(result[0]["id"], irrelevant)

    def test_recall_budget_does_not_truncate_persistent_card(self):
        giant = {**self.card, "mechanism": "Staging " * 10000, "statement": "TPOT " * 10000, "proposed_change": "Backend " * 10000}
        identity = self.register(card=giant)
        result = self.memory.recall(self.brief, max_chars=2500)
        self.assertEqual(len(result), 1)
        self.assertLessEqual(len(json.dumps(result, sort_keys=True, ensure_ascii=False, separators=(",", ":"))), 2500)
        self.assertEqual(self.memory.get(identity)["card"], giant)
        self.assertEqual(self.memory.recall(self.brief, max_chars=50), [])
        self.assertEqual(self.memory.recall(self.brief, limit=0), [])

    def test_running_and_failed_are_queryable_without_claiming_tested_success(self):
        identity = self.register()
        test = self.memory.plan_test(identity, {"run": 1}, self.scope)
        self.memory.start_test(test["id"])
        self.assertEqual(self.memory.query(status="running")[0]["id"], identity)
        self.memory.test_result(test["id"], "error", self.artifact, "Process crashed")
        self.assertEqual(self.memory.query(status="failed")[0]["id"], identity)
        self.assertEqual(self.memory.query(status="tested"), [])
        self.assertEqual(self.memory.query(status="validated"), [])

    def test_legacy_jsonl_preserves_unscoped_outcome_without_claiming_validation(self):
        identity = self.register()
        legacy = self.root / "legacy.jsonl"
        legacy.write_text(json.dumps({"event": "outcome", "run": "run1", "id": "H1", "verdict": "supported", "at": "2026-10-19"}) + "\n")
        self.assertEqual(self.memory.import_jsonl(legacy)["imported"], 1)
        self.assertEqual(self.memory.import_jsonl(legacy)["existing"], 1)
        record = self.memory.get(identity)
        self.assertEqual(record["experiment_status"], "untested")
        self.assertEqual(record["events"][-1]["data"]["legacy_record"]["verdict"], "supported")


if __name__ == "__main__":
    unittest.main()
