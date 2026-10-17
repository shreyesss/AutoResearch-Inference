import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from inference_autoresearch.benchmark import AIPerfAdapter, normalize_exports
from inference_autoresearch.benchmark.aiperf import _percentile
from inference_autoresearch.contracts import MeasurementPolicy, ServerHandle
from inference_autoresearch.workloads import ScenarioRegistry, WorkloadError


class AIPerfAdapterTest(unittest.TestCase):
    def setUp(self):
        self.registry = ScenarioRegistry()
        self.scenario = self.registry.load("qwen-short-chat-r256-v1")

    def test_build_argv_is_frozen_and_uses_native_replay(self):
        adapter = AIPerfAdapter(aiperf_executable=Path(".venv/bin/aiperf"),
                                tokenizer_path=Path(".artifacts/models/Qwen3.8-27B"))
        server = ServerHandle(server_id="test", base_url="http://127.0.0.1:8000", config_id="b0")
        policy = MeasurementPolicy(stage="pilot", replicate=1,
                                   metadata={"benchmark_duration_s": 70, "benchmark_grace_period_s": 60})
        argv = adapter.build_argv(server, self.scenario, policy, Path("/tmp/iar-test-cell"))
        self.assertEqual(argv[argv.index("--custom-dataset-type") + 1], "single-turn")
        self.assertIn("--fixed-schedule", argv)
        self.assertIn("--fixed-schedule-auto-offset", argv)
        self.assertEqual(argv[argv.index("--request-count") + 1], "154")
        self.assertNotIn("--request-rate", argv)
        self.assertEqual(argv[argv.index("--tokenizer") + 1], "Qwen/Qwen3.8-27B")
        self.assertEqual(argv[argv.index("--tokenizer-revision") + 1],
                         "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0")

    def test_offline_aiperf_preflight_loads_exact_pinned_snapshot(self):
        adapter = AIPerfAdapter(aiperf_executable=Path(".venv/bin/aiperf"),
                                tokenizer_path=Path(".artifacts/models/Qwen3.8-27B"))
        with patch.dict(os.environ, {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}):
            receipt = adapter.preflight_tokenizer(self.scenario)
        self.assertEqual(receipt["aiperf_version"], "0.13.0")
        self.assertTrue(receipt["loaded"])
        self.assertEqual(Path(receipt["snapshot"]).resolve(), Path(receipt["snapshot_resolves_to"]))
        self.assertEqual(receipt["network_mode"], "offline")

    def test_offline_cache_must_point_to_pinned_local_model(self):
        with tempfile.TemporaryDirectory() as temp:
            cache = Path(temp) / "cache"
            wrong = Path(temp) / "wrong"
            wrong.mkdir()
            adapter = AIPerfAdapter(aiperf_executable=Path(".venv/bin/aiperf"),
                                    tokenizer_path=Path(".artifacts/models/Qwen3.8-27B"),
                                    tokenizer_cache_dir=cache)
            snapshot = adapter._snapshot_path(self.scenario.metadata["manifest"])
            snapshot.parent.mkdir(parents=True)
            snapshot.symlink_to(wrong, target_is_directory=True)
            with self.assertRaisesRegex(WorkloadError, "another model"):
                adapter.preflight_tokenizer(self.scenario)

    def test_single_sample_percentile_is_sample_value(self):
        self.assertEqual(_percentile([13.5], .99), 13.5)
        self.assertEqual(_percentile([2.0, 4.0, 8.0], .5), 4.0)

    def test_saved_real_export_accounts_for_all_rows(self):
        artifact = Path(".artifacts/sequence-cap-pilot/b0a/r256")
        if not artifact.is_dir():
            self.skipTest("Saved hardware export is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            result = normalize_exports(self.scenario, artifact, config_id="b0", run_id="saved",
                                       output_dir=Path(temp))
            self.assertEqual(result.status, "valid")
            self.assertEqual(result.counts["completed"], 154)
            self.assertEqual(result.counts["successful_completion_tokens"], 154 * 256)
            self.assertAlmostEqual(result.metrics["output_tokens_per_s"], 556.421880607, places=3)
            self.assertGreater(result.metrics["dispatch_lag_p99_ms"], 0)
            self.assertEqual(len((Path(temp) / "normalized-requests.jsonl").read_text().splitlines()), 154)

    def test_missing_export_rows_are_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "profile_export_aiperf.json").write_text(json.dumps({"is_complete": False}))
            result = normalize_exports(self.scenario, directory, config_id="b0", run_id="missing")
            self.assertEqual(result.counts["not_dispatched"], 154)
            self.assertEqual(result.status, "incomplete")
            row = json.loads((directory / "normalized-requests.jsonl").read_text().splitlines()[0])
            self.assertEqual(row["terminal_state"], "not_dispatched")
            self.assertIsNone(row["ttft_ms"])

    def test_measurement_requires_preparation_receipt(self):
        adapter = AIPerfAdapter()
        server = ServerHandle(server_id="test", base_url="http://127.0.0.1:8000", config_id="b0")
        with self.assertRaisesRegex(WorkloadError, "preparation receipt"):
            adapter.run_cell(server, self.scenario, MeasurementPolicy(stage="pilot"), Path("/tmp/iar-no-prep"))

    def test_recorded_trace_uses_native_loader_and_accounts_for_turns(self):
        scenario = self.registry.load("tracelab-four-turn-control-v1")
        adapter = AIPerfAdapter(aiperf_executable=Path(".venv/bin/aiperf"),
                                tokenizer_path=Path(".artifacts/models/Qwen3.8-27B"))
        server = ServerHandle(server_id="test", base_url="http://127.0.0.1:8000", config_id="b0")
        argv = adapter.build_argv(server, scenario, MeasurementPolicy(stage="pilot"), Path("/tmp/iar-trace-cell"))
        self.assertEqual(argv[argv.index("--custom-dataset-type") + 1], "tracelab")
        artifact = Path(".artifacts/workload-controls/tracelab-four-turn")
        if not artifact.is_dir():
            self.skipTest("Saved TraceLab transport export is unavailable")
        with tempfile.TemporaryDirectory() as temp:
            result = normalize_exports(scenario, artifact, config_id="b0", run_id="trace-saved",
                                       output_dir=Path(temp))
            self.assertEqual(result.status, "valid")
            self.assertEqual(result.counts["completed"], 4)
            rows = [json.loads(line) for line in (Path(temp) / "normalized-requests.jsonl").read_text().splitlines()]
            self.assertEqual([row["turn_index"] for row in rows], [0, 1, 2, 3])
            self.assertTrue(all(row["scheduled_arrival_ms"] is None for row in rows))
            self.assertTrue(all(row["source_submission_offset_ms"] is not None for row in rows))

    def test_prepared_mixed_pack_is_pilot_only(self):
        with self.assertRaisesRegex(WorkloadError, "not traffic-validated"):
            self.registry.load("qwen-mixed-prefill-probe-v1")
        scenario = self.registry.load("qwen-mixed-prefill-probe-v1", require_validated=False)
        self.assertEqual(scenario.expected_count, 30)
        adapter = AIPerfAdapter(aiperf_executable=Path(".venv/bin/aiperf"),
                                tokenizer_path=Path(".artifacts/models/Qwen3.8-27B"))
        server = ServerHandle(server_id="test", base_url="http://127.0.0.1:8000", config_id="b0")
        adapter.build_argv(server, scenario, MeasurementPolicy(stage="pilot"), Path("/tmp/iar-mixed-cell"))
        with self.assertRaisesRegex(WorkloadError, "not traffic-validated"):
            adapter.build_argv(server, scenario, MeasurementPolicy(stage="screen"), Path("/tmp/iar-mixed-cell"))


if __name__ == "__main__":
    unittest.main()
