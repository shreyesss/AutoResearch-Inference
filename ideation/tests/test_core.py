import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ideation.github import GitHub, RateLimited
from ideation.research import pack, validate
from ideation.store import Store
from ideation.sources import arxiv_query

class CorpusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "test.sqlite")

    def tearDown(self):
        self.store.db.close()
        self.temp.cleanup()

    def put(self, id="one", **kw):
        doc = dict(id=id, source="test", kind="pr", title="Blackwell DeepSeek V4.1 Flash", body="Improve inter-token latency with speculative decoding", url="https://example.org/1", created_at="2026-01-01T00:00:00Z", updated_at="2026-10-01T00:00:00Z", state="open")
        doc.update(kw)
        self.store.put(doc)
        self.store.db.commit()

    def test_aliases_and_intersection(self):
        self.put()
        self.put("two", title="Hopper attention", body="Reduce TTFT on H100")
        self.assertEqual([r["id"] for r in self.store.search("tpot", tags=["b200", "deepseek-v4.1-flash"])], ["one"])
        self.assertEqual(self.store.search("tpot", tags=["h100"]), [])

    def test_arxiv_boolean_query_not_implicit_or(self):
        self.assertEqual(arxiv_query('"speculative decoding" and serving'), 'all:"speculative decoding" AND all:"serving"')
        self.assertEqual(arxiv_query('ti:"MoE" AND abs:inference'), 'ti:"MoE" AND abs:inference')

    def test_distinct_dates_and_literal_fts(self):
        self.put()
        self.assertEqual(len(self.store.search("", after="2026-09-01", date_field="updated_at")), 1)
        self.assertEqual(len(self.store.search("", after="2026-09-01", date_field="created_at")), 0)
        self.assertEqual(self.store.search('" OR * --'), [])
        with self.assertRaises(ValueError):
            self.store.search(date_field="updated_at; DROP TABLE documents")

    def test_reindex_and_graph_provenance(self):
        self.put(body="B200 https://arxiv.org/abs/2603.03251")
        self.assertTrue(any(e["relation"] == "links_to" for e in self.store.graph("one")))
        self.put(title="H100", body="H100 prefill")
        self.assertEqual(self.store.search("b200"), [])
        self.assertFalse(any(e["relation"] == "links_to" for e in self.store.graph("one")))

    def test_pack_follows_reference_without_parent_metadata(self):
        self.put(id="github:vllm-project/vllm:36037", body="https://arxiv.org/abs/2603.03251")
        self.put(id="fulltext:2603.03251", kind="fulltext", parent="arxiv:2603.03251", body="Paper method and evaluation")
        out = Path(self.temp.name) / "pack"
        pack(self.store, {"seed_numbers": [36037], "queries": []}, str(out))
        ids = {d["id"] for d in json.loads((out / "sources.json").read_text())}
        self.assertIn("fulltext:2603.03251", ids)

    def test_cursor_only_completes_at_end_and_resume(self):
        gh = GitHub(self.store)
        item = {"number": 1, "title": "A", "body": "", "html_url": "https://github.com/vllm-project/vllm/issues/1", "state": "open", "created_at": "2020-01-01T00:00:00Z", "updated_at": "2026-10-01T00:00:00Z"}
        with patch.object(gh, "get", return_value=([item] * 100, {})), patch("ideation.github.time.sleep"):
            gh.sync(feeds=["issues"], max_pages=1)
        state = self.store.get_checkpoint("vllm-project/vllm:issues")
        self.assertTrue(state["in_progress"])
        self.assertEqual(state["page"], 2)
        self.assertNotIn("completed_at", state)
        with patch.object(gh, "get", side_effect=RateLimited("retry")):
            with self.assertRaises(RateLimited):
                gh.sync(feeds=["issues"], max_pages=1)
        self.assertEqual(self.store.get_checkpoint("vllm-project/vllm:issues"), state)
        with patch.object(gh, "get", return_value=([], {})) as getter:
            gh.sync(feeds=["issues"], max_pages=1)
            self.assertEqual(getter.call_args.args[1]["page"], 2)
        self.assertFalse(self.store.get_checkpoint("vllm-project/vllm:issues")["in_progress"])

    def test_opaque_cursor_followed_for_large_collections(self):
        gh = GitHub(self.store)
        item = {"number": 1, "title": "A", "html_url": "https://example.org", "state": "open"}
        cursor = "https://api.github.com/repositories/599547518/issues?after=opaque"
        with patch.object(gh, "get", side_effect=[([item] * 100, {"Link": '<' + cursor + '>; rel="next"'}), ([], {})]) as get, patch("ideation.github.time.sleep"):
            gh.sync(feeds=["issues"], max_pages=2)
            self.assertEqual(get.call_args_list[1].args, (cursor,))

    def test_pr_branch_and_merge_metadata_survive_issue_refresh(self):
        gh = GitHub(self.store)
        p = {"number": 1, "title": "Beam", "body": "NVFP4", "html_url": "https://example.org", "state": "closed", "merged_at": "2026-10-01T00:00:00Z", "base": {"ref": "experimental", "sha": "abc"}, "head": {"ref": "feature", "sha": "def"}}
        gh.ingest(p, "pulls")
        gh.ingest({**p, "pull_request": {}, "merged_at": None}, "issues")
        d = self.store.get("github:vllm-project/vllm:1")
        self.assertEqual(d["metadata"]["base"]["ref"], "experimental")
        self.assertEqual(d["state"], "merged")

    def test_fabricated_citation_rejected(self):
        self.put()
        report = {"hypotheses": [{"id": "H1", "evidence": [{"source_id": "one", "quote": "We measured a 100x speedup"}, {"source_id": "invented", "quote": "anything"}]}]}
        check = validate(self.store, report)
        self.assertFalse(check["valid"])
        self.assertTrue(any("quote not found" in e for e in check["errors"]))
        self.assertTrue(any("unknown source" in e for e in check["errors"]))

if __name__ == "__main__":
    unittest.main()
