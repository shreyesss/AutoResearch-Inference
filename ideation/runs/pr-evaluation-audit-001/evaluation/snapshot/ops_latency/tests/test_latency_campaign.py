from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from lib.serve_pd_recipe import (
    pd_worker_command,
    remove_value_options,
    router_command,
    validate_pd_profile,
)
from lib.serve_recipe import validate_profile, vllm_args
from ops_latency.analyze_latency import analyze, merged_thresholds
from ops_latency.latency_search import (
    SearchError,
    dataset_for_run,
    make_command,
    safe_output_root,
    validate_unique_request_dataset,
)
from ops_latency.prepare_dataset import prepare
from ops_latency.report.build_report import main as build_report
from ops_latency.report.collect_results import (
    apply_repeat_command,
    base_point,
    cache_share,
    collect,
    confirmed_three_run_points,
    mark_pareto_frontier,
    repeated_boundary_passes,
    status_for,
    workload_label,
)
from testing.common.loadgen_shards import parse_args as parse_sharded_args

ROOT = Path(__file__).resolve().parents[2]
IMMUTABLE_HASHES = {
    "serving/b200/vllm/profiles/throughput.yaml": (
        "597fb9353bdfd6d58e2d46eeb3fe05955677d4514f91eff43c75c77e35162c0e"
    ),
    "serving/b200/vllm/profiles/max-throughput.yaml": (
        "d3325719d97ef0e19d6d5f306066f5f9d3508d1072271f67fb6e512af829714f"
    ),
    "serving/b200/vllm/profiles/max-throughput-dep4.yaml": (
        "bb1e45af504e6432d112235fa43d90ee8581146ec8be65255585a7f0d6bfb5b7"
    ),
    "testing/common/loadgen.py": (
        "7ce987f257ee68632d404376032660a705dc2aa402794180c8dac6cc64fdd36c"
    ),
    "source.sh": (
        "6601e69acf645c0786eba3c6b4be3f703cd5da067d8ad2e42ac0dd73771b24f3"
    ),
    "Makefile": (
        "6395f250f19378b7f017183f2f9c322a4f88f4dfe3686f7f3e2b6006c5174612"
    ),
    "testing/common/capacity_search.py": (
        "4ba6fcf4db41ccab5469d956a92c8a3145baf7f52d87d0526597ae31dca38045"
    ),
    "testing/common/run_suite.py": (
        "b268ea1c8fcca1eb44bac3d80c0d368016dac5612a716badf5dfe3e7ce620cb9"
    ),
    "ops/run_screen.sh": (
        "96a7baa23604b064861ecdb7c3b03f9e965d7610e5edb213a44fe6395aeba40c"
    ),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IsolationTests(unittest.TestCase):
    def test_throughput_profiles_and_shared_defaults_are_unchanged(self) -> None:
        for relative, expected in IMMUTABLE_HASHES.items():
            with self.subTest(relative=relative):
                self.assertEqual(sha256(ROOT / relative), expected)

    def test_latency_results_must_use_isolated_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            safe = root / "results" / "latency-campaign" / "LAT-01"
            self.assertEqual(safe_output_root(safe), safe.resolve())
            with self.assertRaises(SearchError):
                safe_output_root(root / "results" / "throughput")

    def test_latency_profiles_are_new_names(self) -> None:
        for name in ("latency-tp4", "latency-dep8"):
            profile = yaml.safe_load(
                (
                    ROOT
                    / f"serving/b200/vllm/profiles/{name}.yaml"
                ).read_text()
            )
            self.assertEqual(profile["name"], name)
            self.assertFalse(profile["features"]["dspark"])
            self.assertFalse(profile["features"]["prefix_caching"])

    def test_recommended_profile_encodes_r7_without_changing_defaults(self) -> None:
        profile = yaml.safe_load(
            (
                ROOT
                / "serving/b200/vllm/profiles/latency-dep8-sla.yaml"
            ).read_text()
        )
        validate_profile(profile)
        self.assertEqual(profile["scheduler"]["max_num_seqs"], 64)
        self.assertEqual(profile["scheduler"]["max_num_batched_tokens"], 16384)
        self.assertEqual(profile["scheduler"]["cuda_graph_max_bs"], 512)
        self.assertTrue(profile["features"]["prefix_caching"])
        self.assertTrue(profile["features"]["dspark"])
        self.assertEqual(
            profile["features"]["dspark_num_speculative_tokens"], 5
        )
        self.assertFalse(
            profile["features"]["dspark_adaptive_verification"]
        )
        with mock.patch.dict(
            "os.environ",
            {
                "MODEL": "test-model",
                "SERVED_MODEL": "test-served-model",
                "MODEL_REVISION": "test-revision",
            },
        ):
            args, _ = vllm_args(
                "b200",
                {"adaptive_verification": True},
                profile,
                8000,
                [],
            )
        speculative = json.loads(
            args[args.index("--speculative-config") + 1]
        )
        self.assertEqual(speculative["num_speculative_tokens"], 5)
        self.assertFalse(speculative["enable_adaptive_verification"])
        self.assertEqual(args[args.index("--api-server-count") + 1], "4")

        legacy = yaml.safe_load(
            (
                ROOT / "serving/b200/vllm/profiles/low-latency.yaml"
            ).read_text()
        )
        with mock.patch.dict(
            "os.environ",
            {
                "MODEL": "test-model",
                "SERVED_MODEL": "test-served-model",
                "MODEL_REVISION": "test-revision",
            },
        ):
            legacy_args, _ = vllm_args(
                "b200",
                {"adaptive_verification": True},
                legacy,
                8100,
                [],
            )
        legacy_speculative = json.loads(
            legacy_args[legacy_args.index("--speculative-config") + 1]
        )
        self.assertEqual(legacy_speculative["num_speculative_tokens"], 5)
        self.assertTrue(
            legacy_speculative["enable_adaptive_verification"]
        )

    def test_campaign_has_every_runner_and_latency_prefixed_flag(self) -> None:
        campaign = yaml.safe_load(
            (ROOT / "ops_latency/campaign.yaml").read_text()
        )
        ids = [item["id"] for item in campaign["experiments"]]
        self.assertEqual(
            ids,
            [
                "LAT-00",
                "LAT-PD-SMOKE",
                "LAT-TP4-BALANCED",
                "LAT-TP4-LOW",
                "LAT-TP4-HYBRID",
                "LAT-PD-BASELINE",
                "LAT-PD-PREFILL16K",
                "LAT-PD-DECODE64",
            ],
        )
        for experiment in campaign["experiments"]:
            with self.subTest(experiment=experiment["id"]):
                self.assertTrue(
                    (ROOT / "ops_latency" / experiment["runner"]).is_file()
                )
        experiments = yaml.safe_load(
            (
                ROOT / "serving/b200/vllm/experiments.yaml"
            ).read_text()
        )["experiments"]
        self.assertIn("lat-dspark-k2", experiments)
        self.assertIn("lat-dspark-k5", experiments)
        recommendation = campaign["measured_recommendation"]
        self.assertEqual(
            recommendation["deployment_profile"],
            "latency-dep8-sla",
        )
        self.assertEqual(
            recommendation["admission"]["recommended_closed_loop_concurrency"],
            384,
        )
        for flag in recommendation["source_experiment_flags"]:
            self.assertIn(flag, experiments)
        router = campaign["vllm_router"]["aggregated_tp4_frontend"]
        self.assertEqual(router["sticky_load_factor"], 1.1)
        self.assertEqual(router["connection_limit"], 4096)
        self.assertEqual(router["retry_connection_errors"], 1)
        comparison = campaign["dep8_vs_2xdep4"]
        self.assertEqual(
            comparison["protocol"]["concurrencies"],
            [256, 384, 512],
        )
        self.assertEqual(
            comparison["protocol"]["dataset_seed_namespace"],
            "dep8-vs-2xdep4-v1",
        )
        self.assertEqual(comparison["corrections"]["maximum"], 2)
        self.assertEqual(
            comparison["arms"]["dep4_api2"]["profile"],
            "latency-2xdep4-sla",
        )
        self.assertTrue(
            (ROOT / "ops_latency" / comparison["runner"]).is_file()
        )
        self.assertTrue(
            all(
                name.startswith("lat-")
                for name in experiments
                if name.startswith("lat-")
            )
        )
        deferred_ids = {
            item["id"] for item in campaign["deferred_experiments"]
        }
        self.assertEqual(
            deferred_ids, {f"LAT-{index:02d}" for index in range(1, 13)}
        )

    def test_pd_profiles_partition_gpus_and_ports(self) -> None:
        for name in (
            "pd-tp4-baseline",
            "pd-tp4-prefill16k",
            "pd-tp4-decode64",
            "pd-tp4-decode128",
        ):
            with self.subTest(name=name):
                profile = yaml.safe_load(
                    (
                        ROOT
                        / f"serving/b200/vllm/pd_profiles/{name}.yaml"
                    ).read_text()
                )
                validate_pd_profile(profile)

    def test_pd_rust_frontend_options_exclude_mm_processor_cache(self) -> None:
        args = [
            "serve",
            "model",
            "--mm-processor-cache-type",
            "shm",
            "--port",
            "8001",
            "--mm-processor-cache-gb",
            "8",
        ]
        self.assertEqual(
            remove_value_options(
                args,
                {"--mm-processor-cache-gb", "--mm-processor-cache-type"},
            ),
            ["serve", "model", "--port", "8001"],
        )

    def test_pd_workers_are_not_privileged_and_keep_gpu_partitions(self) -> None:
        profile = yaml.safe_load(
            (
                ROOT
                / "serving/b200/vllm/pd_profiles/pd-tp4-baseline.yaml"
            ).read_text()
        )
        with (
            mock.patch(
                "lib.serve_pd_recipe.vllm_args",
                return_value=(["serve"], {}),
            ),
            mock.patch(
                "lib.serve_pd_recipe.common_docker",
                return_value=["docker", "run"],
            ) as common_docker,
        ):
            prefill = pd_worker_command(
                profile=profile,
                role_name="prefill",
                base={},
                image="test-image",
            )
            self.assertNotIn("--privileged", prefill)
            self.assertEqual(common_docker.call_args.kwargs["gpu_ids"], "0,1,2,3")
            decode = pd_worker_command(
                profile=profile,
                role_name="decode",
                base={},
                image="test-image",
            )
            self.assertNotIn("--privileged", decode)
            self.assertEqual(common_docker.call_args.kwargs["gpu_ids"], "4,5,6,7")

    def test_pd_variants_change_only_the_intended_scheduler_role(self) -> None:
        root = ROOT / "serving/b200/vllm/pd_profiles"
        baseline = yaml.safe_load(
            (root / "pd-tp4-baseline.yaml").read_text()
        )
        prefill = yaml.safe_load(
            (root / "pd-tp4-prefill16k.yaml").read_text()
        )
        decode = yaml.safe_load(
            (root / "pd-tp4-decode64.yaml").read_text()
        )
        decode128 = yaml.safe_load(
            (root / "pd-tp4-decode128.yaml").read_text()
        )
        self.assertEqual(
            prefill["prefill"]["max_num_batched_tokens"], 16384
        )
        prefill["prefill"]["max_num_batched_tokens"] = 8192
        prefill["name"] = baseline["name"]
        prefill["notes"] = baseline["notes"]
        self.assertEqual(prefill, baseline)
        self.assertEqual(decode["decode"]["max_num_seqs"], 64)
        decode["decode"]["max_num_seqs"] = 32
        decode["name"] = baseline["name"]
        decode["notes"] = baseline["notes"]
        self.assertEqual(decode, baseline)
        self.assertEqual(decode128["decode"]["max_num_seqs"], 128)
        self.assertEqual(decode128["shared"]["cuda_graph_max_bs"], 128)

    def test_pd_router_uses_static_native_worker_urls(self) -> None:
        profile = yaml.safe_load(
            (
                ROOT
                / "serving/b200/vllm/pd_profiles/pd-tp4-baseline.yaml"
            ).read_text()
        )
        with mock.patch.dict(
            "os.environ", {"MODEL_STORAGE_ROOT": "/tmp/model"}
        ):
            command = router_command(profile)
        self.assertIn("--vllm-pd-disaggregation", command)
        self.assertEqual(
            command[command.index("--prefill") + 1],
            "http://127.0.0.1:8001",
        )
        self.assertEqual(
            command[command.index("--decode") + 1],
            "http://127.0.0.1:8002",
        )

    def test_latency_workload_mix_is_capped_and_sums_to_100(self) -> None:
        workload = yaml.safe_load(
            (
                ROOT / "testing/workloads/latency-active-matrix.yaml"
            ).read_text()
        )
        self.assertEqual(len(workload["cases"]), 17)
        self.assertIn(
            "agent-f98",
            {case["name"] for case in workload["cases"]},
        )
        for case in workload["cases"]:
            variants = case.get("variants", [case])
            if "variants" in case:
                self.assertEqual(
                    [variant["weight"] for variant in variants],
                    [45, 20, 15, 20],
                )
            for variant in variants:
                self.assertEqual(
                    variant["min_tokens"], variant["max_tokens"]
                )
                self.assertLessEqual(variant["isl"], 32768)
                self.assertEqual(variant.get("image_share", 0), 0)

    def test_dataset_preparation_adds_affinity_and_warmup(self) -> None:
        record = {
            "max_tokens": 256,
            "min_tokens": 256,
            "ignore_eos": True,
            "_headers": {"X-Session-ID": "old"},
            "_metadata": {
                "case": "chat-f50",
                "actual_isl": 512,
                "actual_prefix_tokens": 256,
                "prefix_key": "zipf-3",
                "max_tokens": 256,
                "min_tokens": 256,
            },
        }
        result = prepare(record, warmup=True)
        self.assertEqual(result["max_tokens"], 1)
        self.assertEqual(result["min_tokens"], 1)
        self.assertEqual(
            result["_metadata"]["target_cacheable_fraction"], 0.5
        )
        self.assertEqual(
            result["_headers"]["X-Session-ID"],
            "cache-chat-f50-zipf-3",
        )

    def test_search_uses_a_distinct_dataset_for_each_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected = root / "open-r8-rep1.jsonl"
            expected.write_text("{}\n")
            args = mock.Mock(
                dataset=None,
                dataset_dir=root,
                plan=False,
            )
            self.assertEqual(
                dataset_for_run(args, "open-r8-rep1"),
                expected.resolve(),
            )
            with self.assertRaisesRegex(SearchError, "missing dataset"):
                dataset_for_run(args, "open-r10-rep1")

    def test_unique_dataset_guard_rejects_repeated_prompts(self) -> None:
        validate_unique_request_dataset(
            {"scheduled": 512, "dataset_requests": 512},
            identifier="open-r8-rep1",
            required=True,
        )
        with self.assertRaisesRegex(
            SearchError, "repeated prompts would invalidate cache"
        ):
            validate_unique_request_dataset(
                {"scheduled": 513, "dataset_requests": 512},
                identifier="open-r8-rep1",
                required=True,
            )

    def test_closed_loop_can_use_sharded_load_generator(self) -> None:
        args = argparse.Namespace(
            mode="closed",
            open_concurrency=4096,
            base_url="http://127.0.0.1:8000/v1",
            model="test-model",
            duration=150,
            timeout=1800,
            max_requests=0,
        )
        with mock.patch.dict(
            "os.environ",
            {"LATENCY_LOADGEN_SHARDS": "8"},
        ):
            command = make_command(
                args=args,
                dataset=Path("/tmp/dataset.jsonl"),
                output_dir=Path("/tmp/output"),
                value=384,
                seed=17,
            )
            self.assertTrue(command[1].endswith("loadgen_shards.py"))
            self.assertEqual(
                command[command.index("--shards") + 1],
                "8",
            )
            parsed = parse_sharded_args(command[2:])
            self.assertEqual(parsed.max_requests, 0)
            self.assertEqual(parsed.seed, 17)
            with self.assertRaisesRegex(SearchError, "must be divisible"):
                make_command(
                    args=args,
                    dataset=Path("/tmp/dataset.jsonl"),
                    output_dir=Path("/tmp/output"),
                    value=386,
                    seed=17,
                )


class AnalysisTests(unittest.TestCase):
    def records(self) -> list[dict[str, object]]:
        return [
            {
                "success": True,
                "ttft_ms": 100.0 * index,
                "tpot_ms": 10.0,
                "e2e_ms": 1000.0,
                "itl_ms": [5.0, 10.0],
                "input_tokens": 512,
                "output_tokens": 10,
                "workload": {"category": "chat", "variant": "short"},
            }
            for index in range(1, 5)
        ]

    def config(self, ttft_p99_ms: float = 500.0) -> dict[str, object]:
        return {
            "slo_tiers": {
                "strict": {
                    "default": {
                        "minimum_samples": 4,
                        "minimum_completion_ratio": 1.0,
                        "maximum_error_rate": 0.0,
                        "ttft_p95_ms": 500.0,
                        "ttft_p99_ms": ttft_p99_ms,
                        "tpot_p95_ms": 20.0,
                        "stream_gap_p99_ms": 20.0,
                        "request_limits": {
                            "ttft_ms": 500.0,
                            "tpot_ms": 20.0,
                            "maximum_stream_gap_ms": 20.0,
                        },
                    }
                }
            }
        }

    def test_post_run_analysis_groups_and_classifies(self) -> None:
        result = analyze(
            records=self.records(),
            summary={
                "mode": "open",
                "run_duration_s": 2.0,
                "queue_slope_ms_per_s": 0.0,
                "concurrency_bound": False,
            },
            slo_config=self.config(),
        )
        self.assertEqual(result["overall"]["completed"], 4)
        self.assertEqual(result["by_category"]["chat"]["scheduled"], 4)
        self.assertEqual(result["overall"]["stream_gap_ms"]["count"], 8)
        self.assertTrue(result["slo_tiers"]["strict"]["pass"])
        self.assertEqual(
            result["slo_tiers"]["strict"]["slo_goodput_rps"], 2.0
        )
        self.assertIn("SSE chunk gap", result["stream_gap_semantics"])

    def test_p99_gate_can_fail_independently(self) -> None:
        result = analyze(
            records=self.records(),
            summary={
                "mode": "open",
                "run_duration_s": 2.0,
                "queue_slope_ms_per_s": 0.0,
                "concurrency_bound": False,
            },
            slo_config=self.config(ttft_p99_ms=200.0),
        )
        tier = result["slo_tiers"]["strict"]
        self.assertFalse(tier["pass"])
        self.assertTrue(
            any("ttft_p99_ms" in reason for reason in tier["reasons"])
        )

    def test_mixed_category_minimum_samples_can_be_advisory(self) -> None:
        records = self.records()
        records[0] = {
            **records[0],
            "workload": {"category": "long-doc"},
        }
        summary = {
            "mode": "open",
            "run_duration_s": 2.0,
            "queue_slope_ms_per_s": 0.0,
            "concurrency_bound": False,
        }
        config = self.config()
        gated = analyze(records=records, summary=summary, slo_config=config)
        self.assertFalse(gated["slo_tiers"]["strict"]["pass"])

        config["slo_tiers"]["strict"][
            "mixed_category_minimum_samples"
        ] = "advisory"
        advisory = analyze(
            records=records,
            summary=summary,
            slo_config=config,
        )
        tier = advisory["slo_tiers"]["strict"]
        self.assertTrue(tier["pass"], tier["reasons"])
        self.assertEqual(
            tier["category_results"]["long-doc"]["insufficient_evidence"],
            "samples 1 < 4",
        )

        # A single-class run still has to meet its sample minimum.
        single = analyze(
            records=self.records()[:3],
            summary=summary,
            slo_config=config,
        )
        self.assertFalse(single["slo_tiers"]["strict"]["pass"])

    def test_class_request_limits_deep_merge(self) -> None:
        tier = {
            "default": {
                "request_limits": {
                    "ttft_ms": 1000,
                    "maximum_stream_gap_ms": 250,
                }
            },
            "class_overrides": {
                "long-doc": {
                    "request_limits": {"ttft_ms": 5000}
                }
            },
        }
        limits = merged_thresholds(tier, "long-doc")["request_limits"]
        self.assertEqual(limits["ttft_ms"], 5000)
        self.assertEqual(limits["maximum_stream_gap_ms"], 250)


class CollectionAndReportTests(unittest.TestCase):
    def test_missing_live_status_is_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            trial = root / "run/cell"
            trial.mkdir(parents=True)
            self.assertEqual(status_for(trial, root), "incomplete")

    def test_closed_loop_point_never_enters_slo_frontier(self) -> None:
        point = base_point(
            summary={
                "mode": "closed",
                "completed": 1,
                "input_tokens": 1,
                "output_tokens": 1,
                "request_rps": 1.0,
            },
            label="closed",
            experiment_id="test",
            evidence_class="test",
            source=Path("/tmp/test"),
            profile="test",
            status="complete",
            cache_hit_share=0.0,
            include_in_slo_frontier=True,
            tier="balanced",
            tier_pass=True,
        )
        self.assertFalse(point["include_in_slo_frontier"])

    def test_three_run_confirmation_and_pareto_marking(self) -> None:
        points = []
        for repetition, phase in ((1, "discovery"), (2, "confirm"), (3, "confirm")):
            points.append(
                {
                    "experiment_id": "LAT-TP4-BALANCED",
                    "profile": "balanced",
                    "arm": None,
                    "workload": "chat",
                    "target_cacheable_fraction": 0.5,
                    "tier": "balanced",
                    "configured_request_rate": 4.0,
                    "evidence_class": "measured_latency_campaign",
                    "scope": "overall",
                    "mode": "open",
                    "repetition": repetition,
                    "pass_phase": phase,
                    "tier_pass": True,
                    "status": "complete",
                    "cache_hit_share": 0.48,
                    "request_rps": 3.9,
                    "slo_goodput_rps": 3.8,
                    "completion_ratio": 1.0,
                    "ttft_p99_ms": 900.0,
                    "tpot_p99_ms": 30.0,
                    "error_rate": 0.0,
                    "source": f"/tmp/rep{repetition}",
                    "label": "fixture",
                }
            )
        confirmed = confirmed_three_run_points(
            points, cache_tolerance=0.10
        )
        self.assertEqual(len(confirmed), 1)
        self.assertTrue(confirmed[0]["decision_grade"])
        mark_pareto_frontier(confirmed)
        self.assertTrue(confirmed[0]["pareto_frontier"])
        self.assertTrue(confirmed[0]["include_in_slo_frontier"])

        dominated = dict(confirmed[0])
        dominated.update(
            {
                "label": "dominated",
                "profile": "slower",
                "ttft_p99_ms": 1000.0,
                "tpot_p99_ms": 35.0,
                "slo_goodput_rps": 3.0,
            }
        )
        values = [confirmed[0], dominated]
        mark_pareto_frontier(values)
        self.assertTrue(values[0]["pareto_frontier"])
        self.assertFalse(values[1]["pareto_frontier"])
        self.assertFalse(values[1]["include_in_slo_frontier"])

    def test_cache_mismatch_excludes_confirmation(self) -> None:
        points = []
        for repetition, phase in ((1, "discovery"), (2, "confirm"), (3, "confirm")):
            points.append(
                {
                    "experiment_id": "LAT-TP4-BALANCED",
                    "profile": "balanced",
                    "arm": None,
                    "workload": "chat",
                    "target_cacheable_fraction": 0.75,
                    "tier": "balanced",
                    "configured_request_rate": 4.0,
                    "evidence_class": "measured_latency_campaign",
                    "scope": "overall",
                    "mode": "open",
                    "repetition": repetition,
                    "pass_phase": phase,
                    "tier_pass": True,
                    "status": "complete",
                    "cache_hit_share": 0.40,
                    "request_rps": 3.9,
                    "slo_goodput_rps": 3.8,
                    "completion_ratio": 1.0,
                    "source": f"/tmp/rep{repetition}",
                    "label": "fixture",
                }
            )
        self.assertEqual(
            confirmed_three_run_points(points, cache_tolerance=0.10),
            [],
        )

    def test_repeat_command_is_emitted_for_balanced_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            live = Path(temporary) / "latency-campaign"
            trial = (
                live
                / "LAT-TP4-BALANCED/20261014/cells/chat-f50/knee/runs/open-r8-rep1"
            )
            point = {
                "pass_phase": "discovery",
                "mode": "open",
                "scope": "overall",
                "tier": "balanced",
                "target_cacheable_fraction": 0.5,
                "configured_request_rate": 8.0,
                "workload": "chat",
            }
            result = apply_repeat_command(point, trial, live)
            self.assertIn("--point chat:50:8", result["repeat_command"])

    def test_pd_cache_share_uses_prefill_metrics_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "metrics-before.txt").write_text(
                "# source http://127.0.0.1:8001/metrics\n"
                'vllm:prefix_cache_hits_total{engine="p"} 0\n'
                'vllm:prefix_cache_queries_total{engine="p"} 0\n'
                "# source http://127.0.0.1:8002/metrics\n"
                'vllm:prefix_cache_hits_total{engine="d"} 0\n'
                'vllm:prefix_cache_queries_total{engine="d"} 0\n'
            )
            (root / "metrics-after.txt").write_text(
                "# source http://127.0.0.1:8001/metrics\n"
                'vllm:prefix_cache_hits_total{engine="p"} 50\n'
                'vllm:prefix_cache_queries_total{engine="p"} 100\n'
                "# source http://127.0.0.1:8002/metrics\n"
                'vllm:prefix_cache_hits_total{engine="d"} 100\n'
                'vllm:prefix_cache_queries_total{engine="d"} 100\n'
            )
            self.assertEqual(cache_share(root), 0.5)

    def test_only_repeated_boundary_summary_qualifies(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            live = Path(temporary) / "latency-campaign"
            trial = live / "LAT-08/run/arms/tp4/chat/boundary/runs/open-r1-rep1"
            trial.mkdir(parents=True)
            boundary = trial.parents[1]
            (boundary / "latency_search_summary.json").write_text(
                json.dumps(
                    {
                        "highest_passing": {
                            "strict": {
                                "load_point": 1.0,
                                "mean_completed_rps": 0.99,
                            }
                        }
                    }
                )
            )
            self.assertTrue(
                repeated_boundary_passes(
                    trial=trial,
                    tier="strict",
                    analysis_summary={"configured_request_rate": 1.0},
                    live_root=live,
                )
            )
            self.assertFalse(
                repeated_boundary_passes(
                    trial=trial,
                    tier="balanced",
                    analysis_summary={"configured_request_rate": 1.0},
                    live_root=live,
                )
            )

    def test_extended_offline_workload_keeps_specific_label(self) -> None:
        path = Path(
            "/results/vllm/throughput/offline-throughput-extended/run/c1"
        )
        self.assertEqual(
            workload_label(path), "offline-throughput-extended"
        )

    def test_imported_open_loop_pass_is_reference_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "archive"
            live = root / "live"
            run = archive / "run"
            trial = run / "default-mix/capacity/runs/open-1"
            trial.mkdir(parents=True)
            summary = {
                "mode": "open",
                "completed": 10,
                "completion_ratio": 1.0,
                "error_rate": 0.0,
                "input_tokens": 100,
                "output_tokens": 50,
                "request_rps": 1.0,
                "ttft_ms": {"p50": 1, "p95": 2, "p99": 3},
                "tpot_ms": {"p50": 1, "p95": 2, "p99": 3},
                "e2e_ms": {"p50": 1, "p95": 2, "p99": 3},
            }
            (trial / "summary.json").write_text(json.dumps(summary))
            capacity = run / "default-mix/capacity/capacity_summary.json"
            capacity.write_text(
                json.dumps(
                    {
                        "run_references": [
                            {"id": "open-1", "pass": True}
                        ]
                    }
                )
            )
            campaign = root / "campaign.yaml"
            campaign.write_text(
                yaml.safe_dump(
                    {
                        "gpu_count": 8,
                        "gpu_price_per_hour": 4.5,
                        "slo_tiers": {},
                        "experiments": [],
                        "existing_evidence": [
                            {
                                "id": "EXP",
                                "label": "fixture",
                                "relative_path": "run",
                                "evidence_class": "reused_cache_hot_slo",
                                "include_in_slo_frontier": True,
                                "profile": "fixture",
                                "cache_hit_share": 0.5,
                            }
                        ],
                    }
                )
            )
            result = collect(
                campaign_path=campaign,
                archive_root=archive,
                live_root=live,
            )
            self.assertEqual(len(result["points"]), 1)
            self.assertFalse(
                result["points"][0]["include_in_slo_frontier"]
            )
            self.assertTrue(result["points"][0]["tier_pass"])

    def test_report_renders_with_empty_experiment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            campaign = root / "campaign.yaml"
            campaign.write_text(
                yaml.safe_dump(
                    {
                        "name": "fixture",
                        "gpu_count": 8,
                        "gpu_price_per_hour": 4.5,
                        "slo_tiers": {},
                        "existing_evidence": [],
                        "experiments": [
                            {
                                "id": "LAT-00",
                                "title": "Fixture",
                                "status": "planned",
                                "objective": "Render an empty table.",
                                "comments": "No values yet.",
                            }
                        ],
                    }
                )
            )
            archive = root / "archive"
            live = root / "latency-campaign"
            archive.mkdir()
            live.mkdir()
            output = root / "report.html"
            self.assertEqual(
                build_report(
                    [
                        "--campaign",
                        str(campaign),
                        "--archive-root",
                        str(archive),
                        "--live-root",
                        str(live),
                        "--output",
                        str(output),
                    ]
                ),
                0,
            )
            rendered = output.read_text()
            self.assertIn("No measured values yet", rendered)
            self.assertIn('id="goodput-chart"', rendered)
            self.assertIn('id="cost-chart"', rendered)
            self.assertIn('id="comparison-ttft-chart"', rendered)
            self.assertIn('id="comparison-tpot-chart"', rendered)


if __name__ == "__main__":
    unittest.main()
