import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ideation.discovery import PaperClient, load_config, plan, refresh, shortlist
from ideation.github import GitHub
from ideation.store import Store


def config():
    return {"version": 1, "repositories": ["owner/engine"], "github_initial_days": None,
            "recency_days": 30, "refresh_hours": 24, "failure_retry_minutes": 30,
            "paper_providers": [], "broad_queries": [], "seeds": [], "queries": [],
            "families": [{"id": "decode", "terms": ["decode"]}], "exploration_fraction": 0.5,
            "budgets": {"github_pages": 1, "pages_per_repository": 1, "paper_requests": 1,
                        "citation_requests": 0, "results_per_query": 10, "shortlist_size": 4}}


def issue(number):
    return {"number": number, "title": "decode performance " + str(number), "body": "Opening body",
            "html_url": "https://github.com/owner/engine/pull/" + str(number), "pull_request": {},
            "state": "open", "created_at": "2020-01-01T00:00:00Z", "updated_at": "2026-10-20T00:00:00Z"}


class FakeGitHub:
    responses = []
    calls = []

    def __init__(self, store, repo):
        self.store, self.repo = store, repo

    def get(self, endpoint, params=None):
        self.calls.append((endpoint, params))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    ingest = GitHub.ingest


class FakePapers:
    calls = []
    responses = []

    def __init__(self, store):
        self.store = store

    def search(self, task, state, limit):
        self.calls.append((copy.deepcopy(task), copy.deepcopy(state), limit))
        return self.responses.pop(0)

    def citations(self, identifier, limit):
        return {"ids": ["arxiv:2001.12345"]}


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "corpus.sqlite")
        FakeGitHub.calls, FakeGitHub.responses = [], []
        FakePapers.calls, FakePapers.responses = [], []

    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()

    def run_refresh(self, cfg, when="2026-10-22T00:00:00Z", **kwargs):
        return refresh(self.store, cfg, now=when, github_factory=FakeGitHub, paper_factory=FakePapers, **kwargs)

    def test_plan_is_offline_and_keeps_distinct_treespark_seeds(self):
        path = Path(__file__).resolve().parents[1] / "config/discovery.json"
        with patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            value = plan(load_config(path))
        seeds = [task for task in value["paper_tasks"] if task["lane"] == "seed"]
        self.assertEqual(len([s for s in seeds if "TreeSpark" in s["seed"]["label"]]), 2)
        self.assertEqual(len(load_config(path)["families"]), 20)

    def test_resume_cursor_and_full_page_without_link_is_complete(self):
        cfg = config()
        next_url = "https://api.github.com/repos/owner/engine/issues?after=opaque"
        FakeGitHub.responses = [([issue(1)], {"Link": '<' + next_url + '>; rel="next"'}),
                                ([issue(i) for i in range(2, 102)], {})]
        first = self.run_refresh(cfg)
        self.assertEqual(first["coverage"][0]["status"], "partial")
        second = self.run_refresh(cfg)
        self.assertEqual(FakeGitHub.calls[1], (next_url, None))
        self.assertEqual(second["coverage"][0]["status"], "completed_pass")
        self.assertEqual(self.store.stats()["documents"], 101)
        self.assertEqual(self.store.get("github:owner/engine:1")["kind"], "pr")
        third = self.run_refresh(cfg)
        self.assertEqual(third["requests"]["github_pages"], 0)

    def test_incremental_overlap_uses_pass_start(self):
        cfg = config()
        FakeGitHub.responses = [([], {}), ([], {})]
        self.run_refresh(cfg)
        self.run_refresh(cfg, "2026-10-24T00:00:00Z")
        self.assertEqual(FakeGitHub.calls[1][1]["since"], "2026-10-21T00:00:00Z")
        self.assertEqual(FakeGitHub.calls[1][1]["sort"], "updated")

    def test_failure_keeps_cursor_and_redacts_secrets_and_has_cooldown(self):
        cfg = config()
        url = "https://api.github.com/repos/owner/engine/issues?after=cursor"
        FakeGitHub.responses = [([issue(1)], {"Link": '<' + url + '>; rel="next"'}), RuntimeError("api_key=SECRET"), ([], {})]
        self.run_refresh(cfg)
        error = self.run_refresh(cfg)
        self.assertNotIn("SECRET", json.dumps(error))
        self.assertEqual(self.run_refresh(cfg)["requests"]["github_pages"], 0)
        self.run_refresh(cfg, "2026-10-22T01:00:00Z")
        self.assertEqual(FakeGitHub.calls[-1], (url, None))
        self.assertIsNotNone(self.store.get("github:owner/engine:1"))

    def test_repositories_rotate_under_budget(self):
        cfg = config()
        cfg["repositories"] = ["owner/one", "owner/two"]
        FakeGitHub.responses = [([], {}), ([], {})]
        self.assertEqual(self.run_refresh(cfg)["coverage"][0]["repo"], "owner/one")
        self.assertEqual(self.run_refresh(cfg)["coverage"][0]["repo"], "owner/two")

    def test_recent_feed_is_available_before_archive_finishes(self):
        cfg = config()
        cfg.update(github_recent_lane=True, github_recent_days=7)
        cfg["budgets"].update(github_pages=2, pages_per_repository=2)
        next_url = "https://api.github.com/repos/owner/engine/issues?after=archive"
        FakeGitHub.responses = [([issue(900)], {}), ([issue(1)], {"Link": '<' + next_url + '>; rel="next"'}), ([], {})]
        result = self.run_refresh(cfg)
        self.assertEqual([r["lane"] for r in result["coverage"]], ["recent", "archive"])
        self.assertEqual(FakeGitHub.calls[0][1]["since"], "2026-10-15T00:00:00Z")
        self.assertEqual(FakeGitHub.calls[0][1]["direction"], "desc")
        self.assertEqual(FakeGitHub.calls[1][1]["direction"], "asc")
        self.assertTrue(result["repository_status"][0]["in_progress"])
        self.assertFalse(result["repository_status"][0]["recent_lane"]["in_progress"])
        self.assertIsNotNone(self.store.get("github:owner/engine:900"))
        self.run_refresh(cfg)
        self.assertEqual(FakeGitHub.calls[-1][0], next_url)

    def test_paper_recency_resume_and_no_repeat_churn(self):
        cfg = config()
        cfg["repositories"] = []
        cfg["broad_queries"] = ["cat:cs.DC"]
        FakePapers.responses = [{"ids": [], "next_cursor": 10}, {"ids": [], "next_cursor": None}]
        self.run_refresh(cfg)
        self.run_refresh(cfg)
        self.assertEqual(FakePapers.calls[0][1]["after"], "2026-09-22")
        self.assertEqual(FakePapers.calls[1][1]["cursor"], 10)
        self.assertEqual(self.run_refresh(cfg)["requests"]["paper_searches"], 0)

    def test_rotating_keyword_query_stays_frozen_until_pagination_finishes(self):
        cfg = config()
        cfg.update(repositories=[], paper_providers=["arxiv"], families=[{"id": "decode", "terms": ["one", "two", "three", "four", "five"]}])
        FakePapers.responses = [{"ids": [], "next_cursor": 10}, {"ids": [], "next_cursor": None}]
        self.run_refresh(cfg)
        self.run_refresh(cfg, "2026-10-24T00:00:00Z")
        self.assertEqual(FakePapers.calls[0][0]["query"], FakePapers.calls[1][0]["query"])
        self.assertEqual(FakePapers.calls[0][1]["after"], FakePapers.calls[1][1]["after"])

    def test_new_user_query_precedes_large_rotation_then_archive_makes_progress(self):
        cfg = config()
        cfg.update(repositories=[], paper_providers=["arxiv"],
                   families=[{"id": str(i), "terms": ["term" + str(i)]} for i in range(60)],
                   queries=[{"provider": "arxiv", "query": "all:targeted-mechanism"}])
        self.store.checkpoint("discovery:paper_rotation", 35)
        FakePapers.responses = [{"ids": [], "next_cursor": 10}, {"ids": [], "next_cursor": None}]
        first = self.run_refresh(cfg)
        self.assertEqual(FakePapers.calls[0][0]["query"], "all:targeted-mechanism")
        self.assertEqual(first["new_user_queries_prioritized"], 1)
        self.assertEqual(self.store.get_checkpoint("discovery:paper_rotation"), 35)
        self.run_refresh(cfg)
        self.assertEqual(FakePapers.calls[1][0]["family"], "35")
        self.assertEqual(self.store.get_checkpoint("discovery:paper_rotation"), 36)

    def test_many_new_user_queries_leave_half_budget_for_normal_rotation(self):
        cfg = config()
        cfg.update(repositories=[], broad_queries=["cat:cs.DC"],
                   queries=[{"provider": "arxiv", "query": "all:user" + str(i)} for i in range(10)])
        cfg["budgets"]["paper_requests"] = 2
        FakePapers.responses = [{"ids": [], "next_cursor": None}, {"ids": [], "next_cursor": None}]
        self.run_refresh(cfg)
        self.assertEqual(FakePapers.calls[0][0]["lane"], "user")
        self.assertEqual(FakePapers.calls[1][0]["lane"], "broad")

    def test_seeds_ignore_recency_and_citations_are_queued_as_unresolved(self):
        cfg = config()
        cfg["repositories"] = []
        cfg["seeds"] = [{"arxiv_id": "2001.00001", "label": "Old seed"}]
        cfg["budgets"]["citation_requests"] = 2
        self.store.put({"id": "arxiv:2001.00001", "source": "arxiv", "kind": "paper", "url": "https://arxiv.org/abs/2001.00001", "title": "Old seed", "body": ""})
        FakePapers.responses = [{"ids": ["arxiv:2001.00001"], "next_cursor": None}, {"ids": [], "next_cursor": None}]
        receipt = self.run_refresh(cfg)
        self.assertIsNone(FakePapers.calls[0][1]["after"])
        self.assertEqual(receipt["coverage"][-1]["unresolved_ids"], ["arxiv:2001.12345"])
        self.assertNotIn("arxiv:2001.12345", receipt["candidate_ids"])
        self.run_refresh(cfg)
        self.assertEqual(FakePapers.calls[-1][0]["lane"], "citation")

    def test_keyword_independent_exploration_keeps_old_unmatched_paper(self):
        cfg = config()
        for i in range(4):
            self.store.put({"id": "paper:" + str(i), "source": "test", "kind": "paper", "url": "https://example.org/" + str(i),
                            "title": "decode" if i < 2 else "Unanticipated method", "body": "", "created_at": "2000-01-01"})
        result = shortlist(self.store, cfg, now="2026-10-22T00:00:00Z")
        self.assertEqual(len(result), 4)
        self.assertEqual(sum(row["selection"] == "exploration" for row in result), 2)
        self.assertTrue(any(not row["matches"] for row in result))
        self.assertTrue(all(row["qualification"] == "not evaluated" for row in result))

    def test_mirrors_deduplicate_without_title_merging_and_weights_configure(self):
        cfg = config()
        cfg["ranking_weights"] = {"lexical": 0, "recency": 100}
        for identifier, metadata in [("arxiv:2610.12345", {}), ("hf:2610.12345", {}),
                                     ("openalex:W123", {"canonical_paper_id": "arxiv:2610.12345"}), ("arxiv:2610.67890", {})]:
            self.store.put({"id": identifier, "source": "test", "kind": "paper", "url": "https://example.org/", "title": "Same title decode", "body": "", "metadata": metadata, "created_at": "2026-10-22"})
        result = shortlist(self.store, cfg, now="2026-10-22T00:00:00Z")
        self.assertEqual(len(result), 2)
        self.assertEqual(sum(len(r["also_seen_as"]) for r in result), 2)
        self.assertTrue(all(row["score_components"]["lexical"] == 0 for row in result))

    def test_arxiv_pagination_stores_version_and_primary_url(self):
        client = PaperClient(self.store)
        raw = b'''<feed xmlns="http://www.w3.org/2005/Atom" xmlns:o="http://a9.com/-/spec/opensearch/1.1/"><o:totalResults>2</o:totalResults><entry><id>http://arxiv.org/abs/2610.20175v2</id><title>A source title</title><summary>Abstract only.</summary><published>2026-10-14T00:00:00Z</published><updated>2026-10-20T00:00:00Z</updated></entry></feed>'''
        with patch.object(client.sources, "request", return_value=(raw, "application/atom+xml")):
            result = client.search({"provider": "arxiv", "query": "cat:cs.DC"}, {"cursor": 0}, 1)
        self.assertEqual(result["next_cursor"], 1)
        doc = self.store.get("arxiv:2610.20175")
        self.assertEqual(doc["metadata"]["arxiv_version"], "2610.20175v2")
        self.assertEqual(doc["metadata"]["read_depth"], "abstract")
        self.assertTrue(doc["url"].startswith("https://arxiv.org/abs/"))


if __name__ == "__main__":
    unittest.main()
