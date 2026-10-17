import hashlib
import importlib.util
import json
from pathlib import Path

from inference_autoresearch.workloads.registry import verify_scenario


ROOT = Path(__file__).resolve().parents[2]


def _freezer():
    path = ROOT / "infra/freeze-ops-synthetic-cell.py"
    spec = importlib.util.spec_from_file_location("ops_freezer", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_freeze_writes_explicit_hashed_request_classes_without_payload_labels(tmp_path):
    freezer = _freezer()
    freezer.ROOT = tmp_path
    cell = tmp_path / "source-cell"
    target = cell / "aiperf/mixed"
    target.mkdir(parents=True)
    preparation = tmp_path / "configs/workloads/ops-preparation.json"
    preparation.parent.mkdir(parents=True)
    preparation.write_text("{}")
    plan = {"workload": "mixed", "request_count": 4, "source_path": "synthetic-mixed.yaml",
            "source_sha256": "source-hash", "offered_rps": 0.1,
            "effective_dataset_entries": 4, "dataset_entry_override": True,
            "arrival": {"pattern": "poisson", "rate_rps": 0.1}, "random_seed": 1042}
    (cell / "plan.json").write_text(json.dumps(plan))
    shapes = [("chat", 512, 256), ("agent", 8192, 1024),
              ("code", 2048, 1024), ("document", 32768, 512)]
    raw, observed = [], []
    for index, (_, prompt_tokens, cap) in enumerate(shapes):
        request_id = f"source-{index}"
        raw.append({"status": 200, "metadata": {"x_request_id": request_id,
                    "credit_issued_ns": 1_000_000_000 + index * 10_000_000_000},
                    "payload": {"messages": [{"role": "user", "content": f"input {index}"}],
                                "model": freezer.MODEL, "ignore_eos": True,
                                "temperature": 0, "max_completion_tokens": cap,
                                "min_tokens": cap}})
        observed.append({"metadata": {"x_request_id": request_id},
                         "metrics": {"usage_completion_tokens": {"value": cap},
                                     "usage_prompt_tokens": {"value": prompt_tokens}}})
    raw_path = target / "profile_export_raw.jsonl"
    raw_path.write_text("".join(json.dumps(row) + "\n" for row in raw))
    (target / "profile_export.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in observed))
    (target / "summary.json").write_text(json.dumps({"status": "complete", "http_200": 4,
        "request_count": 4, "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()}))
    scenario_id = "independent-mixed-test"
    output = tmp_path / "configs/workloads/ops-frozen"
    freezer.freeze(cell, scenario_id, output, "development")
    manifest = json.loads((output / f"{scenario_id}.json").read_text())
    checked = verify_scenario(manifest, root=tmp_path, require_validated=False)
    assert checked["request_classes"] == {
        f"{scenario_id}-{index:05d}": shape for index, (shape, _, _) in enumerate(shapes)}
    assert manifest["request_class_sha256"] == hashlib.sha256(
        (output / f"{scenario_id}.classes.json").read_bytes()).hexdigest()
    assert all("request_class" not in row and "class" not in row for row in checked["planned"])
