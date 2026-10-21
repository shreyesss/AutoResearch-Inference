import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from ideation.deep_dive import investigate
from ideation.github import GitHub
from ideation.sources import Sources
from ideation.store import Store


class DeepDiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "corpus.sqlite")

    def tearDown(self):
        self.store.db.close()
        self.tmp.cleanup()

    def paper(self, identifier="arxiv:2610.10001", metadata=None, body="Abstract", url=None):
        self.store.put({"id": identifier, "source": "test", "kind": "paper", "title": "Paper title",
                        "url": url or "https://arxiv.org/abs/" + identifier.split(":", 1)[1], "body": body,
                        "created_at": "2026-10-14", "updated_at": "2026-10-20", "metadata": metadata or {}})
        self.store.db.commit()
        return identifier

    def run_dive(self, ids, **kwargs):
        return investigate(self.store, "What mechanism can help our deployment?", ids,
                           str(Path(self.tmp.name) / "run"), **kwargs)

    def test_explicit_version_dates_and_fulltext_reasoning_priority(self):
        ids = [self.paper("arxiv:2610." + str(10000 + i)) for i in range(20)]
        self.paper(ids[0], metadata={"arxiv_version": "2610.10000v3"})
        with patch.object(Sources, "_request", return_value=(b"<html><p>Full text with mechanism evidence</p></html>", "text/html")) as fetch, \
             patch("ideation.deep_dive.ResearchTools") as research, \
             patch("ideation.hypotheses.HypothesisTools") as hypothesis:
            research.return_value.evidence.return_value = {"packet": "packet.json"}
            hypothesis.return_value.rubric.return_value = {"path": "rubric.json"}
            hypothesis.return_value.run.return_value = {"status": "reviewed"}
            result = self.run_dive(ids, max_fulltexts=1, max_repositories=0, citations_per_paper=0,
                                   reason=True, brief={"objective": "reduce latency"})
        self.assertEqual(fetch.call_args.args[0], "https://arxiv.org/html/2610.10000v3")
        fulltext = self.store.get("fulltext:2610.10000v3")
        self.assertEqual(fulltext["created_at"], "2026-10-14")
        self.assertEqual(fulltext["updated_at"], "2026-10-20")
        self.assertTrue(fulltext["metadata"]["version_pinned"])
        used_ids = research.return_value.evidence.call_args.args[1]
        self.assertEqual(len(used_ids), 20)
        self.assertEqual(used_ids[0], "fulltext:2610.10000v3")
        self.assertEqual(result["reasoning_omitted_source_ids"], [ids[-1]])

    def test_unpinned_fetch_does_not_claim_old_record_revision_is_current(self):
        identifier = self.paper()
        with patch.object(Sources, "_request", return_value=(b"<html>Full paper</html>", "text/html")):
            result = self.run_dive([identifier], citations_per_paper=0, max_repositories=0)
        fulltext = self.store.get("fulltext:2610.10001")
        self.assertFalse(fulltext["metadata"]["version_pinned"])
        self.assertIsNone(fulltext["updated_at"])
        self.assertEqual(fulltext["metadata"]["source_record_updated_at"], "2026-10-20")

    def test_hf_metadata_and_repository_edges_remain_source_specific(self):
        hf = self.paper("hf:2610.10001", metadata={"githubRepo": "https://github.com/owner/hf-code"})
        unrelated = self.paper("arxiv:2610.10002")
        # The HF mirror inherits the known arXiv revision for the same identity.
        self.paper("arxiv:2610.10001", metadata={"arxiv_version": "2610.10001v2"})

        def fake_init(client, store, repo):
            client.store, client.repo = store, repo

        def fake_get(client, endpoint, params=None):
            if endpoint.startswith("https://api.github.com/repos/"):
                return {"default_branch": "main"}, {}
            if endpoint.startswith("commits/"):
                return {"sha": "a" * 40}, {}
            return [{"name": "README.md", "path": "README.md"}], {}

        def fake_http(client, url, *args, **kwargs):
            if "arxiv.org" in url:
                return b"<html><p>https://github.com/owner/fulltext-code</p></html>", "text/html"
            return b"# Implementation README", "text/plain"

        with patch.object(GitHub, "__init__", fake_init), patch.object(GitHub, "get", fake_get), \
             patch.object(Sources, "_request", fake_http):
            result = self.run_dive([hf, unrelated], max_fulltexts=1, max_repositories=2, citations_per_paper=0)
        edges = list(self.store.db.execute("SELECT src,evidence,detail FROM edges WHERE relation='implementation_candidate'"))
        self.assertEqual(len(edges), 2)
        self.assertTrue(all(row["src"] == hf for row in edges))
        self.assertEqual({row["evidence"] for row in edges}, {hf, "fulltext:2610.10001v2"})
        self.assertEqual(self.store.get(hf)["metadata"]["githubRepo"], "https://github.com/owner/hf-code")
        self.assertEqual(result["reads"][0]["requested_arxiv_id"], "2610.10001v2")

    def test_citation_links_are_not_read_papers_or_reasoning_sources(self):
        identifier = self.paper()
        known = self.paper("arxiv:2001.00001")
        unknown = "arxiv:2001.00002"
        with patch.object(Sources, "_request", return_value=(b"<html>Paper</html>", "text/html")), \
             patch.object(Sources, "citations", return_value={"ids": [known, unknown], "provider": "mock"}):
            result = self.run_dive([identifier], max_repositories=0)
        citations = next(read for read in result["reads"] if "citations" in read)
        self.assertEqual(citations["resolved_ids"], [known])
        self.assertEqual(citations["unresolved_ids"], [unknown])
        self.assertEqual(citations["read_depth"], "bibliographic_links_only")
        self.assertNotIn(known, result["reasoning_source_ids"])
        self.assertNotIn(unknown, result["reasoning_source_ids"])

    def test_cache_miss_budget_stops_second_network_operation(self):
        identifier = self.paper()
        with patch.object(Sources, "_request", return_value=(b"<html>Paper</html>", "text/html")) as request:
            result = self.run_dive([identifier], max_http_calls=1, max_repositories=0, citations_per_paper=1)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(result["http_cache_misses"], 1)
        self.assertTrue(any(error["stage"] == "citations" for error in result["errors"]))

    def test_requested_pinned_file_body_is_available_without_invented_relationship(self):
        identifier = self.paper()
        source = {"repo": "owner/engine", "ref": "a" * 40, "path": "kernels/moe.py"}
        body = b"def dispatch(tokens):\n    return fused_permute(tokens)\n"
        with patch.object(Sources, "_request", return_value=(body, "text/plain")) as request:
            result = self.run_dive([identifier], code_sources=[source], max_fulltexts=0, max_repositories=0)
        expected = "code:owner/engine:" + "a" * 40 + ":kernels/moe.py"
        self.assertEqual(self.store.get(expected)["body"], body.decode())
        self.assertEqual(request.call_args.args[0], "https://raw.githubusercontent.com/owner/engine/" + "a" * 40 + "/kernels/moe.py")
        self.assertIn(expected, result["reasoning_source_ids"])
        self.assertEqual(result["reads"][0]["stage"], "pinned_file")
        self.assertEqual(result["reads"][0]["requested_by"], ["argument"])
        self.assertEqual(list(self.store.db.execute("SELECT * FROM edges WHERE relation='implementation_candidate'")), [])

    def test_brief_code_request_loads_and_shares_http_budget(self):
        identifier = self.paper()
        brief = Path(self.tmp.name) / "brief.json"
        source = {"repo": "owner/engine", "ref": "b" * 40, "path": "sampler.py"}
        brief.write_text(json.dumps({"code_sources": [source]}))
        with patch.object(Sources, "_request", return_value=(b"sampler_code = True", "text/plain")) as request:
            result = self.run_dive([identifier], brief=str(brief), max_http_calls=1, max_repositories=0, citations_per_paper=0)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(result["http_cache_misses"], 1)
        self.assertEqual(result["reads"][0]["requested_by"], ["brief"])
        self.assertTrue(any(item["stage"] == "fulltext" for item in result["errors"]))

    def test_repository_budget_covers_each_paper_before_fulltext_dependency_extras(self):
        first = self.paper("arxiv:2610.20175", body="Project: https://github.com/Robot2050/TreeSpark")
        second = self.paper("arxiv:2609.22098", body="Baselines https://github.com/cited/baseline",
                            metadata={"githubRepo": "PopSoda2002/TreeSpark"})
        requested_repos = []

        def fake_init(client, store, repo):
            client.store, client.repo = store, repo

        def fake_get(client, endpoint, params=None):
            if endpoint.startswith("https://api.github.com/repos/"):
                requested_repos.append(client.repo)
                return {"default_branch": "main"}, {}
            if endpoint.startswith("commits/"):
                return {"sha": "a" * 40}, {}
            return [{"name": "README.md", "path": "README.md"}], {}

        def fake_http(client, url, *args, **kwargs):
            if "arxiv.org" in url:
                return (b"<html>https://github.com/lmarena/arena-hard-auto "
                        b"https://github.com/someone/evaluation "
                        b"https://github.com/another/dependency</html>", "text/html")
            return b"# Project README", "text/plain"

        with patch.object(GitHub, "__init__", fake_init), patch.object(GitHub, "get", fake_get), \
             patch.object(Sources, "_request", fake_http):
            result = self.run_dive([first, second], max_repositories=2, citations_per_paper=0)
        self.assertEqual(requested_repos, ["Robot2050/TreeSpark", "PopSoda2002/TreeSpark"])
        self.assertEqual([row["source_id"] for row in result["repository_selection"]], [first, second])
        self.assertEqual(result["repository_selection"][1]["basis"], "explicit githubRepo metadata")
        edges = self.store.db.execute("SELECT src,dst FROM edges WHERE relation='implementation_candidate'").fetchall()
        self.assertEqual(len(edges), 2)
        self.assertTrue(any(row["src"] == second and "PopSoda2002" in row["dst"] for row in edges))

    def test_citation_provider_failure_is_not_a_successful_empty_read(self):
        identifier = self.paper()
        with patch.object(Sources, "_request", return_value=(b"<html>Paper</html>", "text/html")), \
             patch.object(Sources, "citations", return_value={"error": "HTTP 429", "ids": []}):
            result = self.run_dive([identifier], max_repositories=0)
        receipt = next(item for item in result["reads"] if item.get("stage") == "citations")
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["read_depth"], "not_retrieved")
        self.assertEqual(receipt["error_type"], "ProviderError")
        self.assertIn("no bibliographic coverage", receipt["meaning"])

    def test_argument_and_brief_same_file_deduplicates_without_silent_overwrite(self):
        identifier = self.paper()
        first = {"repo": "owner/engine", "ref": "a" * 40, "path": "sampler.py"}
        second = {**first, "ref": "b" * 40}
        with patch.object(Sources, "_request", return_value=(b"versioned_code = True", "text/plain")) as request:
            result = self.run_dive([identifier], code_sources=[first], brief={"code_sources": [first, second]},
                                   max_fulltexts=0, max_repositories=0)
        # Different explicit pins are meaningful comparison evidence. Preserve
        # both; the brief must not override or silently replace the argument.
        self.assertEqual(request.call_count, 2)
        self.assertEqual(result["pinned_files_requested"], 2)
        pinned = [row for row in result["reads"] if row.get("stage") == "pinned_file"]
        self.assertEqual([row["commit"] for row in pinned], ["a" * 40, "b" * 40])
        self.assertEqual(pinned[0]["requested_by"], ["argument", "brief"])
        self.assertEqual(pinned[1]["requested_by"], ["brief"])

    def test_dict_brief_is_saved_and_passed_as_exact_path_to_rubric_and_hypothesis(self):
        identifier = self.paper()
        brief = {"objective": "Reduce exposed decode latency", "require_novelty": False,
                 "baseline": {"hardware": "H200", "speculative_steps": 5}}
        with patch("ideation.deep_dive.ResearchTools") as research, \
             patch("ideation.hypotheses.HypothesisTools") as hypothesis:
            research.return_value.evidence.return_value = {"packet": "packet.json"}
            hypothesis.return_value.rubric.return_value = {"path": "rubric.json"}
            hypothesis.return_value.run.return_value = {"status": "reviewed"}
            result = self.run_dive([identifier], max_fulltexts=0, max_repositories=0, reason=True, brief=brief)
        path = (Path(self.tmp.name) / "run/brief.json").resolve()
        self.assertEqual(json.loads(path.read_text()), brief)
        self.assertEqual(hypothesis.return_value.rubric.call_args.args[0], str(path))
        self.assertEqual(hypothesis.return_value.run.call_args.args[0], str(path))
        self.assertEqual(result["claim_status"], "reviewed_hypotheses_not_experimentally_validated")

    def test_unpinned_or_too_many_explicit_files_fail_before_network(self):
        identifier = self.paper()
        with patch.object(Sources, "_request") as request:
            with self.assertRaisesRegex(ValueError, "40-hex"):
                self.run_dive([identifier], code_sources=[{"repo": "owner/repo", "ref": "main", "path": "kernel.py"}])
            with self.assertRaisesRegex(ValueError, "max_code_files"):
                self.run_dive([identifier], code_sources=[{"repo": "owner/repo", "ref": "a" * 40, "path": str(i) + ".py"} for i in range(7)])
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
