#!/usr/bin/env python3
"""Freeze a measured ops_aiperf synthetic cell into evaluator-owned native replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from aiperf.dataset.loader.models import SingleTurn


ROOT = Path(__file__).resolve().parents[1]
MODEL = "Qwen/Qwen3.8-27B"
REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
TEMPLATE_HASH = "c3cf9e34abf4f9e36c2d72165aa9c132d3e2a725b6c2586aaa3a8af9d7a81041"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _shape(prompt_tokens: int, output_cap: int) -> str:
    if output_cap == 256 and 256 <= prompt_tokens < 4096:
        return "chat"
    if output_cap == 512 and prompt_tokens >= 16384:
        return "document"
    if output_cap == 1024 and 4096 <= prompt_tokens < 16384:
        return "agent"
    if output_cap == 1024 and 1024 <= prompt_tokens < 4096:
        return "code"
    raise ValueError(f"Unrecognized OPS mixed shape: prompt={prompt_tokens}, output={output_cap}")


def freeze(cell: Path, scenario_id: str, output_dir: Path,
           split: str = "diagnostic") -> dict:
    if split not in ("diagnostic", "development", "sealed_test"):
        raise ValueError(f"Unknown evaluation split: {split}")
    cell = cell.resolve()
    output_dir = output_dir.resolve()
    if not output_dir.is_relative_to(ROOT):
        raise ValueError("Frozen assets must live inside the repository")
    plan = json.loads((cell / "plan.json").read_text())
    workload = plan["workload"]
    aiperf = cell / "aiperf" / workload
    result = json.loads((aiperf / "summary.json").read_text())
    if result["status"] != "complete" or result["http_200"] != result["request_count"]:
        raise ValueError("Only complete HTTP 200 cells can be frozen")
    raw_path = aiperf / "profile_export_raw.jsonl"
    if sha(raw_path) != result["raw_sha256"]:
        raise ValueError("Measured raw export changed")
    raws = read_jsonl(raw_path)
    if len(raws) != plan["request_count"] or any(row["status"] != 200 for row in raws):
        raise ValueError("Source request accounting differs from plan")
    observed = {row["metadata"]["x_request_id"]: row for row in read_jsonl(
        aiperf / "profile_export.jsonl")}
    if len(observed) != len(raws):
        raise ValueError("Metric/request record count differs")
    raws.sort(key=lambda row: row["metadata"]["credit_issued_ns"])
    first = raws[0]["metadata"]["credit_issued_ns"]
    rows = []
    caps = set()
    shape_counts: Counter[str] = Counter()
    classes_by_session_id: dict[str, str] = {}
    for index, raw in enumerate(raws):
        payload = raw["payload"]
        messages = payload.get("messages")
        if (not isinstance(messages, list) or len(messages) != 1
                or messages[0].get("role") != "user"
                or not isinstance(messages[0].get("content"), str)
                or payload.get("model") != MODEL or payload.get("ignore_eos") is not True
                or payload.get("temperature") != 0):
            raise ValueError(f"Unexpected synthetic request at row {index}")
        cap = payload.get("max_completion_tokens")
        if not isinstance(cap, int) or cap < 2:
            raise ValueError(f"Invalid output cap at row {index}")
        metric = observed[raw["metadata"]["x_request_id"]]["metrics"]
        if metric.get("usage_completion_tokens", {}).get("value") != cap:
            raise ValueError(f"Output cap was not realized at row {index}")
        session_id = f"{scenario_id}-{index:05d}"
        if workload == "mixed":
            prompt_tokens = metric.get("usage_prompt_tokens", {}).get("value")
            if type(prompt_tokens) is not int:
                raise ValueError(f"Prompt token count missing at row {index}")
            request_class = _shape(prompt_tokens, cap)
            classes_by_session_id[session_id] = request_class
            shape_counts[request_class] += 1
        caps.add(cap)
        extras = {key: payload[key] for key in ("chat_template_kwargs", "temperature",
                                               "ignore_eos", "min_tokens") if key in payload}
        row = {
            "session_id": session_id,
            "timestamp": round((raw["metadata"]["credit_issued_ns"] - first) / 1e6, 6),
            "text": messages[0]["content"],
            "output_length": cap,
            "extra": extras,
        }
        SingleTurn.model_validate(row)
        rows.append(row)
    if rows[-1]["timestamp"] <= 0:
        raise ValueError("Cannot infer offered load from a zero-duration schedule")
    measured_rate = (len(rows) - 1) * 1000 / rows[-1]["timestamp"]
    asset = output_dir / f"{scenario_id}.jsonl"
    class_sidecar = output_dir / f"{scenario_id}.classes.json"
    card = output_dir / f"{scenario_id}.card.json"
    manifest = output_dir / f"{scenario_id}.json"
    for path in (asset, class_sidecar, card, manifest):
        if path.exists():
            raise ValueError(f"Refusing to overwrite frozen asset: {path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    with asset.open("w") as stream:
        for row in rows:
            stream.write(json.dumps(row, separators=(",", ":")) + "\n")
    if workload == "mixed":
        class_sidecar.write_text(json.dumps({
            "schema_version": "ops-request-classes-v1",
            "scenario_id": scenario_id,
            "classes_by_session_id": classes_by_session_id,
        }, indent=2, sort_keys=True) + "\n")
    card_data = {
        "card_id": scenario_id, "readiness": "prepared", "suite_role": split,
        "source": plan["source_path"], "source_sha256": plan["source_sha256"],
        "source_raw_export": relative(raw_path), "source_raw_sha256": sha(raw_path),
        "workload": workload, "configured_average_rps": plan["offered_rps"],
        "frozen_schedule_average_rps": measured_rate,
        "input_scope": "ops_aiperf synthetic source, Qwen request adapter; exact captured bodies and credits",
        "effective_dataset_entries": plan["effective_dataset_entries"],
        "shape_counts": dict(shape_counts),
        "dataset_entry_override": plan["dataset_entry_override"],
        "cache_protocol": "cold_stream", "traffic_mode": "independent_open_loop",
        "output_policy": "forced_length", "source_arrival": plan["arrival"],
        "realization_evidence": relative(aiperf / "summary.json"),
        "limitations": ["Prepared asset requires an independent fixed-schedule Qwen replay before validation.",
                        "Synthetic mix and request text are diagnostic, not production evidence.",
                        "Observed p99 from this source cell is not an SLA confidence bound."],
    }
    card.write_text(json.dumps(card_data, indent=2, sort_keys=True) + "\n")
    manifest_data = {
        "schema_version": "0.2", "scenario_id": scenario_id,
        "workload_name": f"ops-aiperf-{workload}",
        "workload_group_id": f"ops-aiperf-{workload}-qwen-cold-v1",
        "suite_role": split, "readiness": "prepared",
        "model_id": MODEL, "model_revision": REVISION, "tokenizer_revision": REVISION,
        "template_hash": TEMPLATE_HASH, "protocol_id": "ops-aiperf013-qwen-fresh-warm3-fixed-v1",
        "traffic_mode": "independent_open_loop", "history_mode": "single_turn",
        "load_unit": "requests_per_s", "offered_load": measured_rate,
        "offered_rps": measured_rate, "load_multiplier": 1.0,
        "dispatch_duration_s": rows[-1]["timestamp"] / 1000,
        "n_planned": len(rows), "content_kind": "mechanical",
        "shape_counts": dict(shape_counts),
        "counting_policy": "total_server_prompt_including_template",
        "output_policy": "forced_length",
        "output_tokens_fixed": next(iter(caps)) if len(caps) == 1 else None,
        "input_tokens_total": None, "cache_protocol": "cold_stream",
        "prefix_fraction": 0.0, "prefix_pool_size": 0,
        "dependency_policy_path": None,
        "payload_path": relative(asset), "payload_sha256": sha(asset),
        "schedule_path": relative(asset), "schedule_sha256": sha(asset),
        "workload_card_path": relative(card), "workload_card_sha256": sha(card),
        "preparation_policy_path": "configs/workloads/ops-preparation.json",
        "seeds": {"arrivals": plan.get("random_seed", 42),
                  "content": plan.get("random_seed", 42), "prefix": 0},
        "source_manifest": {"source_id": f"ops_aiperf/{workload}",
                            "revision_or_hash": plan["source_sha256"],
                            "split": split, "characterization_status": "not_applicable",
                            "limitations": ["Synthetic source, not a measured deployment distribution."]},
        "notes": "Frozen from a real B0 source cell; requires independent native replay validation.",
    }
    if workload == "mixed":
        manifest_data["request_class_path"] = relative(class_sidecar)
        manifest_data["request_class_sha256"] = sha(class_sidecar)
    manifest.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n")
    return {"scenario_id": scenario_id, "rows": len(rows), "asset_sha256": sha(asset),
            "source_raw_sha256": sha(raw_path), "frozen_average_rps": measured_rate,
            "paths": [relative(path) for path in (asset, class_sidecar, card, manifest)
                      if path.exists()]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell", type=Path, required=True)
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "configs/workloads/ops-frozen")
    parser.add_argument("--split", choices=("diagnostic", "development", "sealed_test"),
                        default="diagnostic")
    args = parser.parse_args()
    print(json.dumps(freeze(args.cell, args.scenario_id, args.output_dir, args.split), indent=2))


if __name__ == "__main__":
    main()
