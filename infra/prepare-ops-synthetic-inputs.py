#!/usr/bin/env python3
"""Pin the existing ops_aiperf synthetic inputs and print Qwen AIPerf argv.

This only plans inputs. It never starts AIPerf or a model server. The copied
YAML files are byte-for-byte source snapshots, not replacement workloads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "configs/workloads/ops-aiperf-source"
SOURCE = ROOT / "Deepseek_serve/testing/workloads/aiperf"
MODEL = "Qwen/Qwen3.8-27B"
REVISION = "1d4bf0f2ff6012fd82039f2fa52739d0dd7c60c0"
HASHES = {
    "chat": "bde2dede2a8af03a92b8569e8b983b03da5407e351940f0a010acfe227cd36d8",
    "agent": "e157634847d536c7784f24398dce676a543d2d0c371a2496f21cd3fa9fdc727c",
    "code": "01bb2ca2317ce51cbcb03c18fb4ff1c06bb54f82c7e58a1380c37b781b752566",
    "document": "73a46c083a4f9d3b0b6d1b365b1a8e5b18faa98fa99c154c6f6e7e1b59f762c2",
    "mixed": "b5b20ca18420f5246b914d47282e76170b817ded787995094c57190e99da0938",
    "mixed-bursty": "f2e533035ad754b5a836c7ed5d06e02d3dfe1c0268d87be62c5275c7d83b6a8c",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_file(name: str) -> Path:
    path = SNAPSHOT / f"synthetic-{name}.yaml"
    if sha256(path) != HASHES[name]:
        raise ValueError(f"source snapshot changed: {path}")
    original = SOURCE / path.name
    if original.exists() and sha256(original) != HASHES[name]:
        raise ValueError(f"original ops_aiperf source changed: {original}")
    return path


def sequence_distribution(dataset: dict) -> str:
    pairs = []
    for pair in dataset["pairs"]:
        isl = str(pair["input"])
        osl = str(pair["output"])
        if "input_stddev" in pair:
            isl += f"|{pair['input_stddev']}"
        if "output_stddev" in pair:
            osl += f"|{pair['output_stddev']}"
        pairs.append(f"{isl},{osl}:{pair['weight']}")
    if sum(pair["weight"] for pair in dataset["pairs"]) != 100:
        raise ValueError("source weights do not sum to 100")
    return ";".join(pairs)


def plan(name: str, *, rate: float, count: int, duration: float,
         artifact_dir: Path, dataset_entries: int | None = None) -> dict:
    if rate <= 0 or count <= 0 or duration <= 0:
        raise ValueError("rate, count, and duration must be positive")
    path = source_file(name)
    workload = yaml.safe_load(path.read_text())
    if workload["name"] != name or workload["suite"] != "synthetic":
        raise ValueError(f"invalid source workload: {path}")
    dataset, timing = workload["dataset"], workload["timing"]
    if dataset_entries is not None and dataset_entries <= 0:
        raise ValueError("dataset_entries must be positive")
    # Source 'high' is not a Qwen template setting. Qwen's highest setting is
    # 'xhigh'; chat/document/mixed source arms have no reasoning request.
    template = {"enable_thinking": name in ("agent", "code")}
    if template["enable_thinking"]:
        template["reasoning_effort"] = "xhigh"
    extra = {"chat_template_kwargs": template, "ignore_eos": True,
             "temperature": 0}
    args = [
        "profile", "--model", MODEL, "--endpoint-type", "chat",
        "--endpoint", "/v1/chat/completions", "--streaming",
        "--url", "127.0.0.1:8000", "--tokenizer", MODEL,
        "--tokenizer-revision", REVISION, "--apply-chat-template",
        "--use-server-token-count", "--per-chunk-usage",
        "--extra-inputs", json.dumps(extra, separators=(",", ":")),
        "--random-seed", "42", "--request-rate", str(rate),
        "--request-count", str(count), "--benchmark-duration", str(duration),
        "--benchmark-grace-period", "300", "--export-level", "raw",
        "--export-http-trace", "--output-artifact-dir", str(artifact_dir),
    ]
    if dataset["kind"] == "synthetic_text":
        args += ["--prompt-input-tokens-mean", str(dataset["input_tokens_mean"]),
                 "--prompt-input-tokens-stddev", str(dataset["input_tokens_stddev"]),
                 "--prompt-output-tokens-mean", str(dataset["output_tokens_mean"]),
                 "--prompt-output-tokens-stddev", str(dataset["output_tokens_stddev"])]
    elif dataset["kind"] == "sequence_distribution":
        args += ["--sequence-distribution", sequence_distribution(dataset)]
        if dataset.get("maximum_input_tokens"):
            args += ["--synthesis-max-isl", str(dataset["maximum_input_tokens"])]
    else:
        raise ValueError(f"unsupported source dataset: {dataset['kind']}")
    effective_entries = dataset["entries"] if dataset_entries is None else dataset_entries
    args += ["--num-dataset-entries", str(effective_entries)]
    pattern = timing.get("arrival_pattern", "poisson")
    args += ["--arrival-pattern", pattern]
    if pattern == "gamma":
        args += ["--arrival-smoothness", str(timing["arrival_smoothness"])]
    return {
        "source_path": str(path.relative_to(ROOT)),
        "source_sha256": HASHES[name],
        "source_request": workload["request"],
        "qwen_request_adapter": extra,
        "qwen_adapter_note": "Source thinking:true/high maps to Qwen true/xhigh; absent thinking maps to Qwen false. Source token shapes, weights, and arrival law are unchanged.",
        "nominal_dataset": dataset,
        "effective_dataset_entries": effective_entries,
        "dataset_entry_override": dataset_entries is not None,
        "arrival": {"pattern": pattern, "smoothness": timing.get("arrival_smoothness"), "rate_rps": rate},
        "aiperf_args": args,
        "readiness": "input_plan_only; live token/count/schedule validation pending",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", choices=(*HASHES, "all"), default="all")
    parser.add_argument("--request-rate", type=float, required=True)
    parser.add_argument("--request-count", type=int, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--dataset-entries", type=int,
                        help="Calibration-only pool size override; source YAML remains pinned")
    parser.add_argument("--artifact-root", type=Path, required=True)
    args = parser.parse_args()
    names = HASHES if args.workload == "all" else (args.workload,)
    print(json.dumps({name: plan(name, rate=args.request_rate,
                                 count=args.request_count, duration=args.duration,
                                 artifact_dir=args.artifact_root / name,
                                 dataset_entries=args.dataset_entries)
                      for name in names}, indent=2))


if __name__ == "__main__":
    main()
