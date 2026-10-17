import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from inference_autoresearch.workloads import ScenarioRegistry, WorkloadError


class RegistryTest(unittest.TestCase):
    def test_frozen_assets_and_tamper_detection(self):
        source = ScenarioRegistry()
        self.assertEqual(len(source.list()), 4)
        scenario = source.load("qwen-short-chat-r256-v1")
        self.assertEqual(scenario.expected_count, 154)
        self.assertEqual(scenario.offered_load, 2.56)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "configs/workloads").mkdir(parents=True)
            (root / "infra/workloads").mkdir(parents=True)
            for path in (Path("configs/workloads/registry.json"),
                         Path("configs/workloads/short-chat-r256.json"),
                         Path("configs/workloads/short-chat-card.json"),
                         Path("configs/workloads/short-chat-preparation.json"),
                         Path("infra/workloads/b0-chat-r256.jsonl")):
                target = root / path
                target.write_bytes(path.read_bytes())
            registry = ScenarioRegistry(root / "configs/workloads/registry.json")
            self.assertEqual(registry.load("qwen-short-chat-r256-v1").expected_count, 154)
            with (root / "infra/workloads/b0-chat-r256.jsonl").open("a") as stream:
                stream.write("\n")
            with self.assertRaisesRegex(WorkloadError, "changed"):
                registry.load("qwen-short-chat-r256-v1")

    def test_unregistered_scenario_cannot_be_loaded(self):
        with self.assertRaisesRegex(WorkloadError, "Unknown scenario"):
            ScenarioRegistry().load("/tmp/candidate-controlled.json")

    def test_ops_frozen_manifest_loads_after_explicit_registration_and_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "configs/workloads/ops-frozen"
            folder.mkdir(parents=True)
            (root / "configs/workloads/ops-preparation.json").write_text("{}")
            scenario_id = "qwen-ops-mixed-ordinary-v1"
            asset = folder / f"{scenario_id}.jsonl"
            rows = [
                {"session_id": f"{scenario_id}-{index:05d}", "timestamp": timestamp,
                 "text": f"request {index}", "output_length": cap,
                 "extra": {"chat_template_kwargs": {"enable_thinking": index == 1},
                           "temperature": 0, "ignore_eos": True, "min_tokens": cap}}
                for index, (timestamp, cap) in enumerate(((0.0, 256), (60000.0, 1024),
                                                           (121230.0, 512)))
            ]
            asset.write_text("".join(json.dumps(row) + "\n" for row in rows))
            card = folder / f"{scenario_id}.card.json"
            card.write_text(json.dumps({"suite_role": "diagnostic", "readiness": "prepared"}))
            digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
            manifest = json.loads(Path("configs/workloads/mixed-prefill-probe.json").read_text())
            manifest.update({"scenario_id": scenario_id, "workload_name": "ops-aiperf-synthetic-mixed",
                             "readiness": "prepared", "n_planned": 3, "output_tokens_fixed": None,
                             "offered_load": 2000 / 121230, "offered_rps": 2000 / 121230,
                             "dispatch_duration_s": 121.23,
                             "payload_path": str(asset.relative_to(root)), "payload_sha256": digest(asset),
                             "schedule_path": str(asset.relative_to(root)), "schedule_sha256": digest(asset),
                             "workload_card_path": str(card.relative_to(root)),
                             "workload_card_sha256": digest(card),
                             "preparation_policy_path": "configs/workloads/ops-preparation.json"})
            manifest_path = folder / f"{scenario_id}.json"
            manifest_path.write_text(json.dumps(manifest))
            registry_path = root / "configs/workloads/registry.json"
            registry_path.write_text(json.dumps({"version": "workload-registry-v1",
                                                 "scenarios": {scenario_id: str(manifest_path.relative_to(root))}}))
            registry = ScenarioRegistry(registry_path)
            with self.assertRaisesRegex(WorkloadError, "not traffic-validated"):
                registry.load(scenario_id)
            prepared = registry.load(scenario_id, require_validated=False)
            self.assertEqual(prepared.metadata["schedule_duration_s"], 121.23)
            self.assertEqual(prepared.expected_count, 3)
            card.write_text(json.dumps({"suite_role": "diagnostic", "readiness": "validated"}))
            manifest.update({"readiness": "validated", "workload_card_sha256": digest(card)})
            manifest_path.write_text(json.dumps(manifest))
            self.assertEqual(registry.load(scenario_id).metadata["schedule_duration_s"], 121.23)


if __name__ == "__main__":
    unittest.main()
