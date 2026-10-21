import contextlib
import gzip
import hashlib
import io
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ideation.foundation import main
from ideation.store import Store


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state = self.root / "state"

    def tearDown(self):
        self.temporary.cleanup()

    def call(self, *args, state=None, expected=0):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = main(["--state-dir", str(state or self.state), *args])
        self.assertEqual(code, expected, stderr.getvalue())
        return json.loads(stdout.getvalue() if code == 0 else stderr.getvalue())

    def init(self, state=None):
        return self.call("init", state=state)

    def document(self, title="Old draft sampler", updated="2026-10-20T00:00:00Z"):
        return {"id": "github:example/repo:1", "source": "github", "kind": "pr",
                "url": "https://github.com/example/repo/pull/1", "title": title,
                "body": "Speculative decoding sampler draft improvements", "updated_at": updated,
                "fetched_at": updated, "metadata": {"labels": ["performance"], "nested": {"x": 1}}}

    def test_offline_init_plan_imports_no_agent_package(self):
        result = self.init()
        self.assertEqual(result["network_calls"], 0)
        config = json.loads((self.state / "research/config.json").read_text())
        self.assertTrue(config["families"])
        plan = self.call("plan", "--repo", "example/repo", "--query", "draft cache", "--recent-days", "7")
        self.assertEqual(plan["repositories"], ["example/repo"])
        self.assertEqual(plan["recency_days"], 7)
        self.assertFalse((self.state / ".env").exists())
        self.assertEqual(self.call("status")["research"]["documents"], 0)
        self.assertEqual(self.call("bucket-plan")["cloud_actions"], 0)

    def test_sqlite_merge_preserves_newer_local_history_metadata_and_checkpoints(self):
        self.init()
        source_path = self.root / "old.sqlite"
        source = Store(source_path)
        source.put(self.document())
        source.checkpoint("repo:cursor", {"page": 4})
        source.db.close()
        before = hashlib.sha256(source_path.read_bytes()).hexdigest()
        target = Store(self.state / "research/corpus.sqlite")
        target.put(self.document("New sampler", "2026-10-21T00:00:00Z"))
        target.checkpoint("repo:cursor", {"page": 10})
        target.db.close()
        result = self.call("import-corpus", "--source", str(source_path))
        self.assertEqual(result["newer_local_preserved"], 1)
        self.assertEqual(result["checkpoint_conflicts_preserved"], 1)
        self.assertEqual(before, hashlib.sha256(source_path.read_bytes()).hexdigest())
        shown = self.call("show", "github:example/repo:1", "--history")
        self.assertEqual(shown["current"]["title"], "New sampler")
        self.assertIsInstance(shown["current"]["metadata"], dict)
        self.assertTrue(any(row["title"] == "Old draft sampler" for row in shown["revisions"]))
        self.assertEqual(self.call("search", "sampler")[0]["title"], "New sampler")

    def test_gzip_jsonlines_import_is_idempotent_and_preserves_metadata(self):
        self.init()
        source = self.root / "feed.jsonl.gz"
        with gzip.open(source, "wt") as stream:
            stream.write(json.dumps(self.document()) + "\n")
        self.call("import-corpus", "--source", str(source))
        self.call("import-corpus", "--source", str(source))
        self.assertEqual(self.call("status")["research"]["documents"], 1)
        record = self.call("show", "github:example/repo:1", "--history")
        self.assertEqual(record["current"]["metadata"]["nested"], {"x": 1})
        self.assertEqual(len(record["revisions"]), 1)

    def test_publish_restore_and_stale_writer_cannot_adopt_pulled_head(self):
        initial = self.init()["snapshot"]["id"]
        remote = self.root / "remote"
        self.call("push", "--local-remote", str(remote), "--manifest-id", initial)
        replacement = self.root / "replacement"
        self.call("pull", "--local-remote", str(remote), state=replacement)
        self.assertFalse((replacement / "lineage.json").exists())
        self.call("restore", "--manifest-id", initial, state=replacement)
        self.assertEqual(json.loads((replacement / "lineage.json").read_text())["research"]["id"], initial)
        newer = self.call("snapshot")["id"]
        self.call("push", "--local-remote", str(remote), "--manifest-id", newer, "--expected-head", initial)
        self.call("pull", "--local-remote", str(remote), state=replacement)
        stale = self.call("snapshot", state=replacement)["id"]
        # Remote has advanced, but merely pulling does not authorize replacing it.
        self.assertEqual(self.call("push", "--local-remote", str(remote), "--manifest-id", stale,
                                  "--expected-head", newer, state=replacement, expected=1)["error_type"], "ConflictError")
        self.assertEqual(self.call("push", "--local-remote", str(remote), "--manifest-id", stale,
                                  "--expected-head", initial, state=replacement, expected=1)["error_type"], "ConflictError")
        self.call("restore", "--manifest-id", newer, state=replacement, expected=1)

    def test_partial_refresh_snapshots_and_error_message_does_not_leak_key(self):
        self.init()
        def failing_refresh(store, config, **kwargs):
            store.put(self.document())
            store.db.commit()
            raise RuntimeError("https://api.example/?api_key=SECRET_SENTINEL")
        with mock.patch("ideation.discovery.refresh", side_effect=failing_refresh):
            result = self.call("refresh", expected=1)
        self.assertNotIn("SECRET_SENTINEL", json.dumps(result))
        receipts = list((self.state / "research/records").glob("refresh-*/receipt.json"))
        self.assertEqual(len(receipts), 1)
        self.assertEqual(json.loads(receipts[0].read_text())["status"], "failed")
        status = self.call("status")
        self.assertEqual(status["research"]["documents"], 1)
        manifest_id = status["latest_snapshots"]["research"]
        self.assertTrue((self.state / "archives/research/manifests" / (manifest_id + ".json")).exists())

    def test_offline_run_does_not_refresh_and_uses_zero_http_budget(self):
        self.init()
        store = Store(self.state / "research/corpus.sqlite")
        store.put(self.document())
        store.db.commit()
        store.db.close()
        with mock.patch("ideation.discovery.refresh", side_effect=AssertionError("network refresh forbidden")), \
             mock.patch("ideation.deep_dive.investigate", return_value={"status": "dossier_ready"}) as investigate:
            result = self.call("run", "--question", "sampler", "--offline")
        self.assertEqual(investigate.call_args.kwargs["max_http_calls"], 0)
        self.assertEqual(result["selected_sources"], ["github:example/repo:1"])
        self.assertEqual(result["GPU_experiments"], 0)
        self.assertIn("snapshot", result)

    def test_provider_file_allowlist_no_interpolation_or_snapshot_leak(self):
        env_file = self.root / "providers.env"
        env_file.write_text("GITHUB_TOKEN=${SHOULD_NOT_EXPAND}\nUNRELATED_SECRET=NEVER_EXPORT\n")
        with mock.patch.dict(os.environ, {"SHOULD_NOT_EXPAND": "expanded-secret"}, clear=True):
            self.call("--env-file", str(env_file), "init")
            self.assertEqual(os.environ["GITHUB_TOKEN"], "${SHOULD_NOT_EXPAND}")
            self.assertNotIn("UNRELATED_SECRET", os.environ)
        for path in (self.state / "research").rglob("*"):
            if path.is_file():
                self.assertNotIn(b"NEVER_EXPORT", path.read_bytes())

    def test_offline_reason_is_rejected_before_model_or_refresh(self):
        self.init()
        with mock.patch("ideation.discovery.refresh", side_effect=AssertionError("must not refresh")):
            result = self.call("run", "--question", "sampler", "--offline", "--reason", "--brief", "missing.json", expected=1)
        self.assertEqual(result["error_type"], "ValueError")

    def test_timestamp_order_accounts_for_offsets_and_fetch_time_ties(self):
        from ideation.foundation import _document_order
        earlier = {"updated_at": "2026-10-21T06:00:00+05:30", "fetched_at": "2026-10-22T00:00:00Z"}
        later = {"updated_at": "2026-10-21T01:00:00Z", "fetched_at": "2026-10-21T00:00:00Z"}
        self.assertLess(_document_order(earlier), _document_order(later))
        same_update_new_fetch = {**earlier, "fetched_at": "2026-10-23T00:00:00Z"}
        self.assertGreater(_document_order(same_update_new_fetch), _document_order(earlier))

    def test_configured_auto_publication_is_explicit_and_disable_stops_it(self):
        self.init()
        remote = self.root / "auto-remote"
        result = self.call("remote", "configure", "--local-remote", str(remote), "--auto-publish")
        self.assertEqual(result["external_actions"], 0)
        self.assertFalse(remote.exists())
        self.assertTrue(self.call("remote", "show")["remote"]["auto_publish"])
        first = self.call("snapshot")
        self.assertTrue(first["published"])
        second = self.call("snapshot")
        self.assertTrue(second["published"])
        self.assertEqual(second["parent"], first["id"])
        self.assertEqual((remote / "research/HEAD").read_text().strip(), second["id"])
        self.call("remote", "disable")
        local = self.call("snapshot")
        self.assertFalse(local["published"])
        self.assertEqual((remote / "research/HEAD").read_text().strip(), second["id"])

    def test_offline_commands_never_auto_publish(self):
        self.init()
        remote = self.root / "offline-remote"
        self.call("remote", "configure", "--local-remote", str(remote), "--auto-publish")
        init = self.init()
        self.assertFalse(init["snapshot"]["published"])
        run = self.call("run", "--question", "sampler", "--offline")
        self.assertFalse(run["snapshot"]["published"])
        self.assertEqual(run["snapshot"]["publication_skipped"], "offline operation")
        self.assertFalse(remote.exists())

    def test_stale_auto_publication_fails_but_retains_local_snapshot(self):
        self.init()
        remote = self.root / "auto-remote"
        self.call("remote", "configure", "--local-remote", str(remote), "--auto-publish")
        first = self.call("snapshot")["id"]
        other = self.root / "other-writer"
        self.call("pull", "--local-remote", str(remote), state=other)
        self.call("restore", "--manifest-id", first, state=other)
        newer = self.call("snapshot", state=other)["id"]
        self.call("push", "--local-remote", str(remote), "--expected-head", first,
                  "--manifest-id", newer, state=other)
        failure = self.call("snapshot", expected=1)
        self.assertEqual(failure["error_type"], "PublicationError")
        self.assertEqual(failure["publication_error_type"], "ConflictError")
        self.assertTrue(failure["snapshot"]["publication_failed"])
        self.assertFalse(failure["snapshot"]["published"])
        identity = failure["snapshot"]["id"]
        self.assertTrue((self.state / "archives/research/manifests" / (identity + ".json")).exists())
        self.assertEqual(json.loads((self.state / "latest-snapshots.json").read_text())["research"], identity)
        self.assertEqual(json.loads((self.state / "lineage.json").read_text())["research"]["id"], first)
        self.assertEqual((remote / "research/HEAD").read_text().strip(), newer)

    def test_retention_failure_after_event_commit_still_publishes_journal(self):
        remote = self.root / "experiment-remote"
        self.call("remote", "configure", "--local-remote", str(remote), "--auto-publish")
        record = self.root / "experiment.json"
        record.write_text(json.dumps({"experiment_id": "retention-failure", "hypothesis_id": "hypothesis:x", "baseline_id": "baseline:x",
                                     "scope": "component", "provenance": {"source": "retained"}}))
        self.call("experiment", "create", "--record", str(record))
        transition = self.root / "transition.json"
        transition.write_text(json.dumps({"status": "rejected", "note": "Source applicability rejection"}))
        with mock.patch("ideation.experiments.ExperimentRegistry.retain_artifacts", side_effect=OSError("SECRET_COPY_ERROR")):
            failure = self.call("experiment", "transition", "retention-failure", "--record", str(transition), expected=1)
        self.assertEqual(failure["error_type"], "ExperimentMutationError")
        self.assertEqual(failure["mutation_error_type"], "OSError")
        self.assertNotIn("SECRET_COPY_ERROR", json.dumps(failure))
        self.assertTrue(failure["snapshot"]["published"])
        identity = failure["snapshot"]["id"]
        self.assertEqual(self.call("experiment", "get", "retention-failure")["status"], "rejected")
        self.assertTrue((self.state / "archives/experiments/registry/manifests" / (identity + ".json")).exists())
        self.assertEqual((remote / "experiments/registry/HEAD").read_text().strip(), identity)
        replacement = self.root / "journal-recovery"
        self.call("pull", "--namespace", "experiments/registry", "--local-remote", str(remote), state=replacement)
        self.call("restore", "--namespace", "experiments/registry", "--manifest-id", identity, state=replacement)
        recovered = self.call("experiment", "get", "retention-failure", state=replacement)
        self.assertEqual(recovered["status"], "rejected")
        self.assertEqual(len(recovered["events"]), 2)

    def test_experiment_cli_records_scope_and_snapshots_separately(self):
        record = self.root / "experiment.json"
        record.write_text(json.dumps({"experiment_id": "pilot-1", "hypothesis_id": "hypothesis:x", "baseline_id": "baseline:x",
                                     "scope": "component", "provenance": {"source": "retained"}}))
        result = self.call("experiment", "create", "--record", str(record))
        self.assertEqual(result["snapshot"]["namespace"], "experiments/registry")
        self.assertEqual(self.call("experiment", "get", "pilot-1")["status"], "proposed")
        self.assertFalse((self.state / "research").exists())


if __name__ == "__main__":
    unittest.main()
