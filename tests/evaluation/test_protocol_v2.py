import json
from pathlib import Path

import pytest

from inference_autoresearch.evaluation.protocol_v2 import ProtocolError, load_protocol, stage_invocation
from inference_autoresearch.workloads.registry import ScenarioRegistry


def test_v2_screen_is_exact_frozen_mixed_36():
    registry = ScenarioRegistry(Path("configs/workloads/ops4-registry.json"))
    protocol = load_protocol(Path("configs/evaluation-protocol-v2.json"), registry)
    screen = stage_invocation(protocol, "screen")
    assert screen["engine_stage"] == "triage"
    assert screen["request_count"] == 36
    with pytest.raises(ProtocolError, match="no qualified independent workload"):
        stage_invocation(protocol, "sealed_test")


def test_v2_manifest_pin_rejects_drift(tmp_path):
    source = json.loads(Path("configs/evaluation-protocol-v2.json").read_text())
    source["stages"]["screen"]["manifest_sha256"] = "0" * 64
    target = tmp_path / "protocol.json"
    target.write_text(json.dumps(source))
    with pytest.raises(ProtocolError, match="hash changed"):
        load_protocol(target, ScenarioRegistry(Path("configs/workloads/ops4-registry.json")))
