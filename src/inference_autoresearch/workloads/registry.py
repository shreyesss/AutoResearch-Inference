"""Load only evaluator-owned, content-addressed workload manifests.

The registry deliberately has no API for a proposer-supplied path. Native AIPerf
single-turn assets are reused; this module does not regenerate benchmark traffic.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import ScenarioManifest


DEFAULT_REGISTRY = Path("configs/workloads/registry.json")


class WorkloadError(ValueError):
    """A frozen workload is absent, changed, or not ready for measurement."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _asset_path(root: Path, relative: str) -> Path:
    if not relative or Path(relative).is_absolute():
        raise WorkloadError("Asset paths must be relative to the registry root")
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise WorkloadError(f"Asset escapes registry root: {relative}")
    return path


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkloadError(f"Cannot read workload JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise WorkloadError(f"Workload JSON must be an object: {path}")
    return value


def verify_scenario(manifest: dict[str, Any], *, root: Path | None = None,
                    require_validated: bool = True) -> dict[str, Any]:
    """Verify hashes, planned IDs/times, output controls and card readiness.

    Return the parsed planned requests and concrete paths. This is intentionally
    stricter than JSON Schema: schema validity alone does not freeze the traffic.
    """
    root = Path(root or Path.cwd())
    if manifest.get("schema_version") != "0.2":
        raise WorkloadError("Unsupported scenario contract version")
    if require_validated and manifest.get("readiness") != "validated":
        raise WorkloadError(f"Scenario not traffic-validated: {manifest.get('scenario_id')}")
    traffic_mode = manifest.get("traffic_mode")
    if traffic_mode == "independent_open_loop":
        if manifest.get("history_mode") != "single_turn" or manifest.get("load_unit") != "requests_per_s" or manifest.get("output_policy") != "forced_length":
            raise WorkloadError("Invalid independent single-turn traffic declaration")
    elif traffic_mode == "dependent_sessions":
        if manifest.get("history_mode") != "recorded" or manifest.get("load_unit") != "active_users" or manifest.get("output_policy") != "natural_eos":
            raise WorkloadError("Invalid recorded dependent-session declaration")
    else:
        raise WorkloadError("Unsupported traffic mode")
    if manifest.get("cache_protocol") != "cold_stream":
        raise WorkloadError("Cache preparation needs a separate validated implementation")
    payload = _asset_path(root, manifest["payload_path"])
    schedule = _asset_path(root, manifest["schedule_path"])
    card = _asset_path(root, manifest["workload_card_path"])
    preparation = _asset_path(root, manifest["preparation_policy_path"])
    for name, path, expected in (
        ("payload", payload, manifest["payload_sha256"]),
        ("schedule", schedule, manifest["schedule_sha256"]),
        ("card", card, manifest["workload_card_sha256"]),
    ):
        if not path.is_file() or sha256_file(path) != expected:
            raise WorkloadError(f"Frozen {name} asset missing or changed: {path}")
    if not preparation.is_file():
        raise WorkloadError("Preparation policy is missing")
    card_data = _read_json(card)
    if card_data.get("suite_role") != manifest.get("suite_role") or card_data.get("readiness") != manifest.get("readiness"):
        raise WorkloadError("Card and manifest readiness/role disagree")
    if payload != schedule:
        raise WorkloadError("Pinned native replay expects one schedule/payload file")
    rows = []
    try:
        with payload.open() as stream:
            for line in stream:
                if line.strip():
                    rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError) as exc:
        raise WorkloadError(f"Invalid JSONL asset: {exc}") from exc
    if len(rows) != manifest["n_planned"]:
        raise WorkloadError("Planned request count differs from frozen asset")
    ids = [row.get("session_id") for row in rows]
    if any(not isinstance(value, str) or not value for value in ids):
        raise WorkloadError("Planned session IDs are missing")
    if traffic_mode == "independent_open_loop":
        times = [row.get("timestamp") for row in rows]
        if len(set(ids)) != len(ids):
            raise WorkloadError("Independent request IDs are duplicated")
        if any(not isinstance(value, (float, int)) or value < 0 for value in times):
            raise WorkloadError("Planned timestamps must be nonnegative milliseconds")
        if times != sorted(times) or abs(times[0]) > 1e-9:
            raise WorkloadError("Planned timestamps must start at zero and increase")
        expected_tokens = manifest["output_tokens_fixed"]
        if any(not isinstance(row.get("text"), str)
               or not isinstance(row.get("output_length"), int)
               or row["output_length"] < 2
               or (expected_tokens is not None and row["output_length"] != expected_tokens)
               for row in rows):
            raise WorkloadError("Frozen rows lack matching text/output length")
        actual_rps = (len(rows) - 1) * 1000 / times[-1]
        if abs(actual_rps - manifest["offered_load"]) > 0.001:
            raise WorkloadError("Offered load differs from fixed schedule")
    else:
        keys = [(row.get("session_id"), row.get("round_index")) for row in rows]
        if len(set(keys)) != len(keys):
            raise WorkloadError("Dependent session/turn IDs are duplicated")
        by_session: dict[str, list[int]] = {}
        for row in rows:
            turn = row.get("round_index")
            cap = (row.get("output_tokens") or 0) + (row.get("reasoning_output_tokens") or 0)
            if not isinstance(turn, int) or not isinstance(cap, int) or cap < 2:
                raise WorkloadError("TraceLab row lacks a valid turn index/output cap")
            by_session.setdefault(row["session_id"], []).append(turn)
        if any(indices != list(range(len(indices))) for indices in by_session.values()):
            raise WorkloadError("Dependent turns must be complete and ordered within session")
    return {"payload_path": payload, "schedule_path": schedule,
            "card_path": card, "preparation_path": preparation, "planned": rows,
            "card": card_data}


class ScenarioRegistry:
    """Evaluator-owned lookup for prepared scenarios; no arbitrary scenario paths."""

    def __init__(self, registry_path: Path = DEFAULT_REGISTRY, *, root: Path | None = None):
        registry_path = Path(registry_path).resolve()
        self.root = Path(root).resolve() if root is not None else registry_path.parents[2]
        registry = _read_json(registry_path)
        if registry.get("version") != "workload-registry-v1":
            raise WorkloadError("Unsupported workload registry version")
        self._paths = registry.get("scenarios", {})
        if not isinstance(self._paths, dict):
            raise WorkloadError("Invalid scenario registry")

    def list(self) -> list[str]:
        return sorted(self._paths)

    def load(self, scenario_id: str, *, require_validated: bool = True) -> ScenarioManifest:
        if scenario_id not in self._paths:
            raise WorkloadError(f"Unknown scenario: {scenario_id}")
        path = _asset_path(self.root, self._paths[scenario_id])
        data = _read_json(path)
        if data.get("scenario_id") != scenario_id:
            raise WorkloadError("Registry key differs from scenario ID")
        checked = verify_scenario(data, root=self.root, require_validated=require_validated)
        return ScenarioManifest(
            scenario_id=scenario_id,
            workload_id=data["workload_name"],
            path=path,
            group_id=data["workload_group_id"],
            offered_load=data["offered_load"],
            load_unit=data["load_unit"],
            expected_count=data["n_planned"],
            output_policy=data["output_policy"],
            traffic_mode=data["traffic_mode"],
            history_mode=data["history_mode"],
            cache_protocol=data["cache_protocol"],
            metadata={"manifest": data, "asset": str(checked["payload_path"]),
                      "registry_root": str(self.root)},
        )
