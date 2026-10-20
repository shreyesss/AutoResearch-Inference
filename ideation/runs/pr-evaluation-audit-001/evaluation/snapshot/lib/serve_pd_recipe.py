#!/usr/bin/env python3
"""Launch same-node TP4 prefill/decode workers with native vllm-router."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    from .serve_recipe import (
        ROOT,
        common_docker,
        csv_count,
        image_for,
        load_yaml,
        vllm_args,
        wait_ready,
    )
except ImportError:  # Direct script execution.
    from serve_recipe import (
        ROOT,
        common_docker,
        csv_count,
        image_for,
        load_yaml,
        vllm_args,
        wait_ready,
    )


ENGINE_ROOT = ROOT / "serving/b200/vllm"
PD_PROFILES = ENGINE_ROOT / "pd_profiles"


def remove_value_options(args: list[str], options: set[str]) -> list[str]:
    """Remove CLI options and their following values."""
    filtered: list[str] = []
    index = 0
    while index < len(args):
        argument = args[index]
        if argument in options:
            if index + 1 >= len(args):
                raise ValueError(f"missing value for {argument}")
            index += 2
            continue
        filtered.append(argument)
        index += 1
    return filtered


def validate_pd_profile(profile: dict[str, Any]) -> None:
    required = {"schema_version", "name", "topology", "shared", "prefill", "decode", "router"}
    missing = sorted(required - set(profile))
    if missing:
        raise SystemExit(f"PD profile missing keys: {', '.join(missing)}")
    topology = profile["topology"]
    if topology != {"tp": 4, "dp": 1, "ep": 1, "expert_parallel": False}:
        raise SystemExit("same-node PD profiles must use TP4/DP1/EP1")
    roles = [profile["prefill"], profile["decode"]]
    gpu_sets: list[set[int]] = []
    http_ports: set[int] = set()
    side_ports: set[int] = set()
    for role in roles:
        gpu_ids = str(role["gpu_ids"])
        if csv_count(gpu_ids) != 4:
            raise SystemExit(f"PD role must expose four GPUs: {gpu_ids}")
        gpu_set = {int(value) for value in gpu_ids.split(",")}
        if len(gpu_set) != 4 or not gpu_set <= set(range(8)):
            raise SystemExit(f"invalid PD GPU IDs: {gpu_ids}")
        gpu_sets.append(gpu_set)
        port = int(role["port"])
        if port in http_ports:
            raise SystemExit(f"duplicate PD HTTP port: {port}")
        http_ports.add(port)
        base = int(role["nixl_side_channel_port"])
        role_side_ports = set(range(base, base + 4))
        if side_ports & role_side_ports:
            raise SystemExit("prefill/decode NIXL side-channel ranges overlap")
        side_ports.update(role_side_ports)
        if int(role["max_num_seqs"]) <= 0 or int(role["max_num_batched_tokens"]) <= 0:
            raise SystemExit("PD scheduler limits must be positive")
    if gpu_sets[0] & gpu_sets[1] or gpu_sets[0] | gpu_sets[1] != set(range(8)):
        raise SystemExit("PD roles must partition GPUs 0-7 without overlap")
    router_port = int(profile["router"]["port"])
    if router_port in http_ports:
        raise SystemExit("PD router port overlaps a worker HTTP port")


def role_profile(profile: dict[str, Any], role_name: str) -> dict[str, Any]:
    role = profile[role_name]
    shared = profile["shared"]
    return {
        "schema_version": 1,
        "name": profile["name"],
        "topology": profile["topology"],
        "replicas": [{"gpu_ids": role["gpu_ids"], "port": role["port"]}],
        "scheduler": {
            "max_model_len": shared["max_model_len"],
            "max_num_seqs": role["max_num_seqs"],
            "max_num_batched_tokens": role["max_num_batched_tokens"],
            "cuda_graph_max_bs": shared["cuda_graph_max_bs"],
            "chunked_prefill_size": role["max_num_batched_tokens"],
            "max_prefill_tokens": role["max_num_batched_tokens"],
        },
        "features": {
            "dspark": False,
            "prefix_caching": bool(shared["prefix_caching"]),
            "bounded_replay": False,
            "engram_host": bool(shared["engram_host"]),
            "mm_processor_cache_gb": int(shared["mm_processor_cache_gb"]),
            "hicache": False,
        },
    }


def pd_worker_command(
    *,
    profile: dict[str, Any],
    role_name: str,
    base: dict[str, Any],
    image: str,
) -> list[str]:
    role = profile[role_name]
    generated_profile = role_profile(profile, role_name)
    engine_args, engine_env = vllm_args(
        "b200", base, generated_profile, int(role["port"]), []
    )
    # The Rust frontend rejects these multimodal processor-cache options.
    # Active PD workloads are text-only, so omitting them does not alter the
    # measured model or KV-transfer behavior.
    engine_args = remove_value_options(
        engine_args,
        {"--mm-processor-cache-gb", "--mm-processor-cache-type"},
    )
    kv_role = "kv_producer" if role_name == "prefill" else "kv_consumer"
    engine_args.extend(
        [
            "--kernel-config",
            json.dumps(
                {"enable_flashinfer_autotune": False},
                separators=(",", ":"),
            ),
            "--kv-transfer-config",
            json.dumps(
                {
                    "kv_connector": "NixlConnector",
                    "kv_role": kv_role,
                    "kv_load_failure_policy": "fail",
                },
                separators=(",", ":"),
            ),
        ]
    )
    engine_env.update(
        {
            "NCCL_CUMEM_ENABLE": "1",
            "NCCL_MNNVL_ENABLE": "1",
            "NCCL_NVLS_ENABLE": "1",
            "UCX_NET_DEVICES": "all",
            "VLLM_DEEP_GEMM_WARMUP": "skip",
            "VLLM_NIXL_SIDE_CHANNEL_HOST": "127.0.0.1",
            "VLLM_NIXL_SIDE_CHANNEL_PORT": str(
                role["nixl_side_channel_port"]
            ),
            "VLLM_USE_RUST_FRONTEND": "1",
        }
    )
    command = common_docker(
        name=f"dsv41-b200-vllm-{profile['name']}-{role_name}",
        gpu_ids=str(role["gpu_ids"]),
        image=image,
        engine="vllm",
        extra_env=engine_env,
        engine_args=engine_args,
        nsys_output=None,
    )
    return command


def router_command(profile: dict[str, Any]) -> list[str]:
    router = profile["router"]
    default = (
        Path(os.environ["MODEL_STORAGE_ROOT"])
        / "tools/vllm-router/bin/vllm-router"
    )
    binary = os.environ.get("VLLM_ROUTER_BIN", str(default))
    return [
        binary,
        "--policy",
        str(router["policy"]),
        "--vllm-pd-disaggregation",
        "--prefill",
        f"http://127.0.0.1:{profile['prefill']['port']}",
        "--decode",
        f"http://127.0.0.1:{profile['decode']['port']}",
        "--host",
        str(router["host"]),
        "--port",
        str(router["port"]),
        "--intra-node-data-parallel-size",
        "1",
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--stop", action="store_true")
    args = parser.parse_args()

    profile_path = PD_PROFILES / f"{args.profile}.yaml"
    profile = load_yaml(profile_path)
    validate_pd_profile(profile)
    if profile["name"] != args.profile:
        raise SystemExit("PD profile name must match its filename")
    if args.validate:
        print(f"validated b200/vllm/pd/{args.profile}")
        return

    names = [
        f"dsv41-b200-vllm-{profile['name']}-prefill",
        f"dsv41-b200-vllm-{profile['name']}-decode",
    ]
    if args.stop:
        subprocess.run(["docker", "rm", "-f", *names], check=False)
        return
    if not args.dry_run and os.environ.get("SKIP_PREFLIGHT", "0") != "1":
        subprocess.run(
            ["bash", str(ROOT / "ops/preflight.sh"), "b200"], check=True
        )

    base = load_yaml(ENGINE_ROOT / "base.yaml")
    images = load_yaml(ENGINE_ROOT / "images.yaml")
    image = image_for("vllm", images)
    worker_commands = [
        pd_worker_command(
            profile=profile,
            role_name=role_name,
            base=base,
            image=image,
        )
        for role_name in ("prefill", "decode")
    ]
    pd_router_command = router_command(profile)
    if args.dry_run:
        for command in worker_commands:
            print(shlex.join(command))
        print(shlex.join(pd_router_command))
        return

    router_binary = pd_router_command[0]
    if not (
        Path(router_binary).is_file() or shutil.which(router_binary) is not None
    ):
        raise SystemExit(
            "native vllm-router is unavailable; set VLLM_ROUTER_BIN to "
            "the pinned router binary"
        )

    processes: list[subprocess.Popen[Any]] = []

    def stop_all(*_: object) -> None:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
        for process in reversed(processes):
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()

    def handle_signal(signum: int, _: object) -> None:
        stop_all()
        raise SystemExit(128 + signum)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    try:
        for command in worker_commands:
            processes.append(subprocess.Popen(command))
        wait_ready(
            f"http://127.0.0.1:{profile['prefill']['port']}",
            processes,
        )
        wait_ready(
            f"http://127.0.0.1:{profile['decode']['port']}",
            processes,
        )
        processes.append(subprocess.Popen(pd_router_command))
        wait_ready(
            f"http://127.0.0.1:{profile['router']['port']}",
            processes,
        )
        while True:
            for process in processes:
                exit_code = process.poll()
                if exit_code is not None:
                    raise SystemExit(exit_code)
            time.sleep(2)
    finally:
        stop_all()


if __name__ == "__main__":
    main()
