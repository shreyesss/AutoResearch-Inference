"""Offline B0 importer rejects mismatched native requests and reports class latency."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "infra/import_fast_b0.py"
SPEC = importlib.util.spec_from_file_location("import_fast_b0", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _trial(tmp_path: Path, *, tamper: bool = False) -> tuple[Path, dict, dict, dict]:
    directory = tmp_path / "native"
    directory.mkdir()
    planned = [
        {"session_id": "a", "text": "chat prompt", "output_length": 256,
         "extra": {"temperature": 0}},
        {"session_id": "b", "text": "code prompt", "output_length": 1024,
         "extra": {"temperature": 0}},
    ]
    raw = []
    measured = []
    for index, row in enumerate(planned):
        native_id = f"native-{index}"
        raw.append({"status": 200, "metadata": {"x_request_id": native_id},
                    "payload": {"model": "Qwen/test", "messages": [
                        {"role": "user", "content": row["text"]}],
                        "max_completion_tokens": row["output_length"],
                        "temperature": 1 if tamper and index == 1 else 0}})
        measured.append({"metadata": {"x_request_id": native_id}, "metrics": {
            "usage_completion_tokens": {"value": row["output_length"]},
            "time_to_first_token": {"unit": "ms", "value": 100 + 50 * index},
            "inter_token_latency": {"unit": "ms", "value": 20 + 5 * index}}})
    summary = {"is_complete": True, "input_config": {"phases": [
        {"name": "profiling", "type": "poisson", "requests": 2, "rate": 0.1}]},
        "request_throughput": {"avg": 0.1}, "output_token_throughput": {"avg": 10}}
    (directory / "profile_export_aiperf.json").write_text(json.dumps(summary))
    (directory / "profile_export_raw.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in raw))
    (directory / "profile_export.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in measured))
    manifest = {"model_id": "Qwen/test"}
    verified = {"planned": planned, "request_classes": {"a": "chat", "b": "code"}}
    policy = {"schema_version": "0.1", "policy_id": "test", "confidence_level": 0.95,
              "classes": {name: {"percentile": "p90", "ttft_ms": 200, "tpot_ms": 30,
                                 "max_error_fraction": 0, "min_eligible_requests": 1}
                          for name in ("chat", "code")}}
    return directory, manifest, verified, policy


def test_imported_class_metrics_and_hashes(tmp_path: Path) -> None:
    directory, manifest, verified, policy = _trial(tmp_path)
    result = MODULE.inspect_trial(directory, kind="source_capture", manifest=manifest,
                                  verified=verified, policy=policy)
    assert result["status"] == "valid"
    assert result["classes"]["chat"]["ttft_p50_ms"] == 100
    assert result["classes"]["code"]["ttft_p90_ms"] == 150
    assert result["classes"]["code"]["tpot_p90_ms"] == 25
    assert len(result["native_artifacts"]["profile_export_raw.jsonl"]["sha256"]) == 64
    assert result["observed_feasible"] is False  # Two requests cannot support a p90 claim.


def test_rejects_changed_output_control(tmp_path: Path) -> None:
    directory, manifest, verified, policy = _trial(tmp_path, tamper=True)
    with pytest.raises(ValueError, match="output controls"):
        MODULE.inspect_trial(directory, kind="source_capture", manifest=manifest,
                             verified=verified, policy=policy)
