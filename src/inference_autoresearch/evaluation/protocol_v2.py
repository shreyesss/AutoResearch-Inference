"""Versioned sample policy for the exploratory OPS mixed evaluation.

The protocol never promotes the 36-request screen into a tail or SLA finding.
It describes which executable stages have qualified inputs today; later stages
must name their own frozen manifests before they can be run.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from inference_autoresearch.workloads.registry import ScenarioRegistry, sha256_file


class ProtocolError(ValueError):
    pass


def load_protocol(path: Path, registry: ScenarioRegistry) -> dict[str, Any]:
    path = Path(path)
    raw = json.loads(path.read_text())
    if raw.get("protocol_id") != "ops-mixed-v2-exploratory" or raw.get("version") != 2:
        raise ProtocolError("Unsupported evaluation protocol")
    stages = raw.get("stages")
    if not isinstance(stages, dict):
        raise ProtocolError("Protocol stages must be an object")
    screen = stages.get("screen", {})
    if screen.get("engine_stage") != "triage" or screen.get("request_count") != 36:
        raise ProtocolError("The qualified mixed screen is the 36-request triage cell")
    scenario = registry.load(screen.get("scenario_id", ""))
    if scenario.expected_count != screen["request_count"]:
        raise ProtocolError("Screen request count differs from frozen scenario")
    if sha256_file(Path(scenario.path)) != screen.get("manifest_sha256"):
        raise ProtocolError("Screen scenario manifest hash changed")
    if screen.get("claim") != "large_regression_screen_only":
        raise ProtocolError("Small screen cannot support tail or SLA claims")
    adaptive = stages.get("adaptive_exploration", {})
    if adaptive.get("scenario_id") != scenario.scenario_id:
        raise ProtocolError("Adaptive exploration must use the same frozen input corpus")
    if adaptive.get("request_count") != scenario.expected_count:
        raise ProtocolError("Each adaptive point must consume the complete frozen corpus")
    if adaptive.get("repeats", 0) < 1 or adaptive.get("iterations", 0) < 2:
        raise ProtocolError("Adaptive trial and iteration budgets must be positive")
    for stage_name in ("development_replication", "sealed_test"):
        stage = stages.get(stage_name, {})
        if stage.get("status") != "awaiting_independent_manifest":
            raise ProtocolError(f"{stage_name} must have independently frozen content before activation")
    return raw


def stage_invocation(protocol: dict[str, Any], stage_name: str) -> dict[str, Any]:
    stage = protocol["stages"].get(stage_name)
    if stage is None:
        raise ProtocolError(f"Unknown protocol stage: {stage_name}")
    if stage.get("status") == "awaiting_independent_manifest":
        raise ProtocolError(f"{stage_name} has no qualified independent workload yet")
    return dict(stage)
