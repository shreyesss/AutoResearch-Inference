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


if __name__ == "__main__":
    unittest.main()
