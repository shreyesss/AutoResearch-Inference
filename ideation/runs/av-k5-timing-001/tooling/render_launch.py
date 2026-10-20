#!/usr/bin/env python3
"""Render only: frozen baseline plus evaluator observation and Torch profiling."""

import hashlib
import json
from pathlib import Path
import shlex


ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "av-k5"
BASELINE = ROOT / "c03/rendered-rollback-backends.txt"
ORIGINAL = Path(
    "/home/ubuntu/AutoResearch-Inference-c03/ideation/runs/"
    "c03-execution-001/original-baseline-commands.txt"
)
IMAGE = (
    "vllm/vllm-openai@sha256:"
    "3d17635c5aa0340e2f2502c067ce4b587d8e7dc678195e90b71142490dc6d71c"
)
ALLOWED = {
    "vllm/v1/worker/gpu/model_runner.py",
    "vllm/v1/worker/gpu/spec_decode/dflash/speculator.py",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docker_commands(path):
    return [
        tokens
        for line in path.read_text().splitlines()
        if (tokens := shlex.split(line))[:2] == ["docker", "run"]
    ]


def main():
    manifest_path = HERE / "observation-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["image"] == IMAGE
    assert len(manifest["files"]) == 2
    assert {entry["path"] for entry in manifest["files"]} == ALLOWED
    mounts = []
    for entry in manifest["files"]:
        source = (HERE / entry["source"]).resolve()
        assert source.is_relative_to(HERE / "source/observation")
        assert source.is_file() and digest(source) == entry["sha256"]
        assert digest(ROOT / "c03/source/base" / entry["path"]) == entry["base_sha256"]
        assert not source.stat().st_mode & 0o222, "observation source must be frozen"
        destination = "/usr/local/lib/python3.12/dist-packages/" + entry["path"]
        mounts.extend([
            "--mount", f"type=bind,src={source},dst={destination},readonly"
        ])

    originals = docker_commands(BASELINE)
    assert len(originals) == 2 and originals == docker_commands(ORIGINAL)
    records = []
    for replica, original in enumerate(originals):
        assert original.count(IMAGE) == 1
        assert "--profiler-config" not in original
        assert "--mount" not in original
        assert not any("C03_" in token or "PYTHONPYCACHEPREFIX=" in token
                       for token in original)
        spec = json.loads(original[original.index("--speculative-config") + 1])
        assert spec == {
            "method": "dspark", "num_speculative_tokens": 5,
            "draft_sample_method": "probabilistic",
            "rejection_sample_method": "block",
            "enable_adaptive_verification": False,
        }
        profiler = {
            "profiler": "torch",
            "torch_profiler_dir": f"/profiles/av-k5-timing-001/replica{replica}",
            "torch_profiler_activities": ["CPU", "CUDA"],
            "torch_profiler_with_stack": False,
            "torch_profiler_record_shapes": False,
            "torch_profiler_with_memory": False,
            "torch_profiler_with_flops": False,
            "torch_profiler_use_gzip": True,
            "torch_profiler_dump_cuda_time_total": False,
            "ignore_frontend": True,
            "capture_torch_profiler": False,
            "detailed_trace_annotation": False,
            "delay_iterations": 0,
            "warmup_iterations": 1,
            "active_iterations": 20,
            "wait_iterations": 0,
            "max_iterations": 20,
        }
        image_index = original.index(IMAGE)
        additions = mounts + ["-e", "PYTHONPYCACHEPREFIX=/tmp/av-k5-pycache"]
        command = original[:image_index] + additions + original[image_index:] + [
            "--profiler-config", json.dumps(profiler, separators=(",", ":"))
        ]
        restored = command[:image_index] + command[image_index + len(additions):-2]
        assert restored == original
        records.append({"replica": replica, "argv": command,
                        "profiler_config": profiler,
                        "original_argv_sha256": hashlib.sha256(
                            json.dumps(original, separators=(",", ":")).encode()
                        ).hexdigest(),
                        "only_declared_additions": True})

    result = {
        "schema_version": 1,
        "purpose": "AV-OFF k5 timing only; render does not launch anything",
        "image": IMAGE,
        "baseline_command_file_sha256": digest(BASELINE),
        "original_command_file_sha256": digest(ORIGINAL),
        "observation_manifest_sha256": digest(manifest_path),
        "observation_files": manifest["files"],
        "router": "independently preserved by root; no router command rendered",
        "commands": records,
    }
    (HERE / "rendered-backends.json").write_text(json.dumps(result, indent=2) + "\n")
    (HERE / "rendered-backends.txt").write_text(
        "\n".join(shlex.join(row["argv"]) for row in records) + "\n"
    )
    print(json.dumps({"rendered": 2, "source_mounts_per_replica": 2,
                      "original_arguments_preserved": True,
                      "adaptive_verification": False,
                      "result": str(HERE / "rendered-backends.json")}))


if __name__ == "__main__":
    main()
