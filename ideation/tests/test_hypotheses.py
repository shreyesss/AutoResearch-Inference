import tempfile
import unittest
from pathlib import Path

from ideation.evidence import canonical, quote_errors, ResearchTools, grounded_excerpt
from ideation.hypotheses import CARD, assess, fingerprint, HypothesisTools
from ideation.policy import validate_policy, review_schema
import json
from unittest.mock import patch
from ideation.store import Store


class HypothesisGateTests(unittest.TestCase):
    def setUp(self):
        self.sources = [
            {"id": "github:vllm-project/vllm:1", "kind": "pr", "title": "Serving", "body": "The draft waits for verification to finish."},
            {"id": "fulltext:2603.03251", "kind": "fulltext", "title": "Study", "body": "Overlap can reduce the critical path under these conditions."},
        ]
        self.card = {k: "Specific proposed behavior" for k in CARD["required"]}
        self.card.update(id="H1", parents=[], operation="generate", classification="adaptation",
                         alternatives=[{"explanation": "The gain is only batching", "distinguishing_test": "Hold batch size fixed"}],
                         evidence=[{"source_id": d["id"], "quote": d["body"], "relation": "supports"} for d in self.sources],
                         novelty={k: "Bounded difference, unproven" for k in CARD["properties"]["novelty"]["required"]},
                         experiment={k: "Explicit criterion" for k in CARD["properties"]["experiment"]["required"]})
        self.policy = {
            "objective": "Improve TPOT against current deployment", "baseline_comparison": "Current dispatch",
            "novelty_required": False, "novelty_request": "",
            "criteria": [
                {"id": "baseline_value", "description": "Useful delta or cheap baseline inspection", "category": "improvement", "weight": 70, "required": True, "justification": "Task objective"},
                {"id": "test_cost", "description": "Cheap discriminating test", "category": "testability", "weight": 30, "required": False, "justification": "Limited budget"},
            ], "threshold": 60,
            "evidence": {"minimum_independent_sources": 1, "require_engineering": True, "require_paper_fulltext": False, "rationale": "Engineering transfer"},
            "retrieval": {"github": False, "literature": False, "rationale": "Packet is sufficient for this test"},
            "rationale": "Prioritize deployment benefit and cheap tests"
        }
        self.review = {"id": "H1", "criteria": {c["id"]: {"verdict": "pass", "score": 4, "rationale": "Grounded useful test"} for c in self.policy["criteria"]},
                       "factual_support": "pass", "objections": [], "required_revision": "None"}
        self.prior = {"github": {"ids": ["one"]}, "literature": {"ids": ["two"]}}

    def check(self):
        return assess(self.card, self.review, self.sources, self.prior, policy=self.policy)

    def test_high_score_cannot_override_task_constraint(self):
        self.review["criteria"]["baseline_value"].update(verdict="fail", score=5)
        result = self.check()
        self.assertFalse(result["eligible"])
        self.assertEqual(result["status"], "rejected")

    def test_unknown_defers_instead_of_invalidating(self):
        self.review["criteria"]["baseline_value"]["verdict"] = "unknown"
        self.assertEqual(self.check()["status"], "deferred")

    def test_known_ports_and_repeated_ideas_can_be_eligible_without_paper(self):
        self.card["classification"] = "upstream_port"
        self.card["evidence"] = self.card["evidence"][:1]
        self.sources = self.sources[:1]
        self.prior = {}
        self.assertTrue(assess(self.card, self.review, self.sources, {}, {fingerprint(self.card)}, policy=self.policy)["eligible"])

    def test_rubric_weights_and_requirements_are_task_specific(self):
        self.review["criteria"]["baseline_value"]["score"] = 5
        self.review["criteria"]["test_cost"]["score"] = 0
        self.assertEqual(self.check()["score"], 70)
        self.policy["criteria"][0]["weight"] = 20
        self.policy["criteria"][1]["weight"] = 80
        self.assertEqual(self.check()["score"], 20)
        self.assertEqual(self.check()["status"], "deferred")
        self.policy["evidence"]["require_paper_fulltext"] = True
        self.card["evidence"] = self.card["evidence"][:1]
        self.assertTrue(any("paper" in r for r in self.check()["reasons"]))

    def test_novelty_opt_in_and_no_silent_weight(self):
        criterion = {"id": "originality", "description": "Publication distinction", "category": "novelty", "weight": 0, "required": True, "justification": "Requested"}
        self.policy["criteria"].append(criterion)
        with self.assertRaises(ValueError):
            validate_policy(self.policy, {})
        self.policy.update(novelty_required=True, novelty_request="Require publication novelty")
        validate_policy(self.policy, {"instructions": "Require publication novelty"})
        with self.assertRaises(ValueError):
            validate_policy(self.policy, {"selection": {"require_novelty": False}})
        self.review["criteria"]["originality"] = {"verdict": "fail", "score": 0, "rationale": "Known mechanism"}
        self.assertEqual(self.check()["status"], "rejected")

    def test_generated_discovery_is_not_primary_evidence(self):
        self.sources[0]["kind"] = "discovery"
        result = self.check()
        self.assertFalse(result["eligible"])
        self.assertIn("Generated discovery output cannot be primary evidence", result["reasons"])

    def test_two_mirrors_are_one_source(self):
        self.policy["evidence"]["minimum_independent_sources"] = 2
        self.sources[0].update(id="hf:2603.03251", kind="paper")
        self.card["evidence"][0]["source_id"] = "hf:2603.03251"
        self.assertEqual(canonical(self.sources[0]), canonical(self.sources[1]))
        self.assertTrue(any("independent" in s for s in self.check()["reasons"]))

    def test_html_and_browser_reads_are_one_source(self):
        self.policy["evidence"]["minimum_independent_sources"] = 2
        for i, source in enumerate(self.sources):
            source.update(id="fathom:read:" + str(i), kind="resource", url="https://docs.sglang.ai/")
            self.card["evidence"][i]["source_id"] = source["id"]
        self.assertTrue(any("independent" in s for s in self.check()["reasons"]))

    def test_fabricated_quote_and_absent_prior_art_reject(self):
        self.card["evidence"][0]["quote"] = "Invented measured 200 percent improvement"
        self.prior["literature"]["ids"] = []
        reasons = self.check()["reasons"]
        self.assertTrue(any("Quote not found" in r for r in reasons))
        self.assertFalse(any("Prior-art" in r for r in reasons))

    def test_missing_alternative_or_inconclusive_rule_reject(self):
        self.card["alternatives"] = []
        self.card["experiment"]["inconclusive_if"] = ""
        self.assertFalse(self.check()["eligible"])

    def test_schema_rejects_out_of_range_scores(self):
        self.review["criteria"]["test_cost"]["score"] = 100
        self.assertFalse(self.check()["eligible"])

    def test_valid_proposal_is_only_eligible_for_test_design(self):
        result = self.check()
        self.assertTrue(result["eligible"])
        self.assertEqual(result["score"], 80)
        self.assertIn("not scientifically validated", result["meaning"])
        self.assertTrue(assess(self.card, self.review, self.sources, self.prior, {fingerprint(self.card)}, policy=self.policy)["eligible"])

    def test_run_retains_proposal_when_critic_crashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            store = Store(root / "corpus.sqlite")
            tool = HypothesisTools(store)
            (root / "brief.json").write_text(json.dumps({"count": 1, "selection": {"require_novelty": False}}))
            (root / "packet.json").write_text(json.dumps({"sources": self.sources, "claims": [], "quote_validation": {"valid": True}}))
            with patch("ideation.hypotheses.run_agent", side_effect=[{"hypotheses": [self.card], "gaps": []}, RuntimeError("critic unavailable")]):
                with self.assertRaisesRegex(RuntimeError, "critic unavailable"):
                    tool.run(str(root / "brief.json"), str(root / "packet.json"), str(root / "run"), policy=self.policy)
            memory = tool.memory()
            self.assertEqual(len(memory), 1)
            self.assertEqual(memory[0]["status"], "proposed")
            self.assertEqual(memory[0]["card"], self.card)
            self.assertEqual(json.loads((root / "run/manifest.json").read_text())["status"], "failed")
            tool.ledger.db.close()
            store.db.close()

    def test_prefix_filter_applies_before_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder) / "test.sqlite")
            for id in ["arxiv:1", "github:vllm-project/vllm:1", "github:other/repo:1"]:
                store.put(dict(id=id, source="test", kind="paper", title="B200", body="Inference", url="https://example.org"))
            self.assertEqual([d["id"] for d in store.search("B200", limit=1, id_prefix="github:vllm-project/vllm:")], ["github:vllm-project/vllm:1"])
            store.db.close()

    def test_publication_window_excludes_unknown_and_upper_bound(self):
        self.assertFalse(ResearchTools._within({"created_at": None}, "2026-01-01", None))
        self.assertFalse(ResearchTools._within({"created_at": "2026-10-01"}, None, "2026-10-01"))
        self.assertTrue(ResearchTools._within({"created_at": "2026-09-30"}, "2026-01-01", "2026-10-01"))

    def test_critic_receives_quote_beyond_default_excerpt(self):
        doc = {"id": "github:1", "kind": "pr", "body": "x" * 8000 + "\nFull path TPOT did not improve.\n" + "y" * 2000}
        cited = [{"source_id": "github:1", "quote": "Full path TPOT did not improve."}]
        self.assertIn(cited[0]["quote"], grounded_excerpt(doc, cited))
        self.assertNotIn("Made up measurement", grounded_excerpt(doc, [{"source_id": "github:1", "quote": "Made up measurement"}]))


if __name__ == "__main__":
    unittest.main()
