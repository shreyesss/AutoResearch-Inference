#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"missing configuration: {path}")
    payload = yaml.safe_load(path.read_text())
    if not isinstance(payload, dict):
        raise SystemExit(f"configuration must be a mapping: {path}")
    return payload


def validate_profile(profile: dict[str, Any]) -> None:
    schema = json.loads((ROOT / "config/schema/profile.schema.json").read_text())
    jsonschema.validate(profile, schema)
    expected_gpus = int(profile["topology"]["tp"]) * int(
        profile["topology"]["dp"]
    )
    seen_gpus: set[int] = set()
    seen_ports: set[int] = set()
    seen_rpc_ports: set[int] = set()
    replicas = profile["replicas"]
    require_rpc_port = len(replicas) > 1 and int(profile["topology"]["dp"]) > 1
    for index, replica in enumerate(replicas):
        gpu_ids = [int(value) for value in str(replica["gpu_ids"]).split(",")]
        if len(gpu_ids) != expected_gpus:
            raise jsonschema.ValidationError(
                f"replica {index}: GPU count does not match TP×DP topology"
            )
        if len(set(gpu_ids)) != len(gpu_ids):
            raise jsonschema.ValidationError(
                f"replica {index}: duplicate GPU IDs are not allowed"
            )
        overlap = seen_gpus.intersection(gpu_ids)
        if overlap:
            raise jsonschema.ValidationError(
                f"replica {index}: GPUs already assigned: {sorted(overlap)}"
            )
        seen_gpus.update(gpu_ids)

        port = int(replica["port"])
        if port in seen_ports:
            raise jsonschema.ValidationError(
                f"replica {index}: duplicate backend port {port}"
            )
        seen_ports.add(port)

        replica_args = [str(value) for value in replica.get("extra_args") or []]
        rpc_ports: list[str] = []
        for position, value in enumerate(replica_args):
            if value == "--data-parallel-rpc-port":
                if position + 1 >= len(replica_args):
                    raise jsonschema.ValidationError(
                        f"replica {index}: --data-parallel-rpc-port needs a value"
                    )
                rpc_ports.append(replica_args[position + 1])
        if require_rpc_port and len(rpc_ports) != 1:
            raise jsonschema.ValidationError(
                f"replica {index}: multi-replica DP profiles require one "
                "--data-parallel-rpc-port"
            )
        for value in rpc_ports:
            try:
                rpc_port = int(value)
            except ValueError as exc:
                raise jsonschema.ValidationError(
                    f"replica {index}: invalid data-parallel RPC port {value!r}"
                ) from exc
            if not 1024 <= rpc_port <= 65535:
                raise jsonschema.ValidationError(
                    f"replica {index}: data-parallel RPC port is out of range"
                )
            if rpc_port in seen_rpc_ports or rpc_port in seen_ports:
                raise jsonschema.ValidationError(
                    f"replica {index}: duplicate/colliding RPC port {rpc_port}"
                )
            seen_rpc_ports.add(rpc_port)
    collisions = seen_ports.intersection(seen_rpc_ports)
    if collisions:
        raise jsonschema.ValidationError(
            f"backend and data-parallel RPC ports overlap: {sorted(collisions)}"
        )


def csv_count(value: str) -> int:
    return len([item for item in value.split(",") if item])


def image_for(engine: str, images: dict[str, Any]) -> str:
    override = os.environ.get(f"{engine.upper()}_IMAGE", "")
    return override or str(images["default"])


def selected_experiments(
    path: Path, requested: list[str], profile_name: str
) -> tuple[list[str], dict[str, str]]:
    if not requested:
        return [], {}
    payload = load_yaml(path)
    definitions = payload.get("experiments") or {}
    args: list[str] = []
    env: dict[str, str] = {}
    for name in requested:
        if name not in definitions:
            raise SystemExit(f"unknown experiment {name!r} in {path}")
        item = definitions[name]
        if item.get("classification") in {"benchmark-only", "output-changing"}:
            print(
                f"WARNING: experiment {name} is {item['classification']}",
                file=sys.stderr,
            )
        if profile_name in (item.get("incompatible_profiles") or []):
            raise SystemExit(f"experiment {name} is incompatible with {profile_name}")
        args.extend(str(value) for value in item.get("args") or [])
        env.update({str(key): str(value) for key, value in (item.get("env") or {}).items()})
    return args, env


def common_docker(
    *,
    name: str,
    gpu_ids: str,
    image: str,
    engine: str,
    extra_env: dict[str, str],
    engine_args: list[str],
    nsys_output: str | None,
) -> list[str]:
    storage = Path(os.environ["MODEL_STORAGE_ROOT"])
    hf_home = Path(os.environ["HF_HOME"])
    engine_cache = Path(os.environ["ENGINE_CACHE_ROOT"]) / engine
    profiler_cache = Path(os.environ["PROFILER_CACHE_ROOT"])
    for path in (storage, hf_home, engine_cache, profiler_cache):
        path.mkdir(parents=True, exist_ok=True)

    command = [
        "docker",
        "run",
        "--rm",
        "--name",
        name,
        "--gpus",
        f'"device={gpu_ids}"',
        "--network",
        "host",
        "--ipc",
        "host",
        "--shm-size",
        "64g",
        "--ulimit",
        "memlock=-1",
        "--ulimit",
        "stack=67108864",
        "--cap-add",
        "IPC_LOCK",
        "-e",
        "HF_HOME=/root/.cache/huggingface",
        "-e",
        f"NCCL_DEBUG={os.environ.get('NCCL_DEBUG', 'WARN')}",
        "-e",
        "PYTHONHASHSEED=0",
        "-v",
        f"{hf_home}:/root/.cache/huggingface",
        "-v",
        f"{engine_cache}:/root/.cache/{engine}",
        "-v",
        f"{profiler_cache}:/profiles",
    ]
    if os.environ.get("HF_TOKEN"):
        command.extend(["-e", "HF_TOKEN"])
    for key, value in sorted(extra_env.items()):
        command.extend(["-e", f"{key}={value}"])
    executable = "vllm" if engine == "vllm" else "sglang"
    if nsys_output:
        command.extend(["--entrypoint", "nsys"])
    else:
        command.extend(["--entrypoint", executable])
    command.append(image)
    if nsys_output:
        command.extend(
            [
                "launch",
                "--session-new",
                f"{nsys_output}-{name}",
                "-t",
                "cuda,nvtx,osrt,nccl",
                "--cuda-graph-trace",
                "graph",
                executable,
            ]
        )
    command.extend(engine_args)
    return command


def vllm_args(
    hardware: str,
    base: dict[str, Any],
    profile: dict[str, Any],
    port: int,
    experiment_args: list[str],
) -> tuple[list[str], dict[str, str]]:
    model = os.environ["MODEL"]
    served = os.environ["SERVED_MODEL"]
    revision = os.environ["MODEL_REVISION"]
    is_nvfp4 = "nvfp4" in model.lower() or "nvfp4" in served.lower()
    topology = profile["topology"]
    scheduler = profile["scheduler"]
    features = profile.get("features") or {}

    args = [
        "serve",
        model,
        "--revision",
        revision,
        "--served-model-name",
        served,
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--tensor-parallel-size",
        str(topology["tp"]),
        "--tokenizer-mode",
        "deepseek_v41",
        "--reasoning-parser",
        "deepseek_v41",
        "--tool-call-parser",
        "deepseek_v41",
        "--enable-auto-tool-choice",
        "--mm-encoder-tp-mode",
        "data",
        "--mm-processor-cache-type",
        "shm",
        "--mm-processor-cache-gb",
        str(features.get("mm_processor_cache_gb", 8)),
        "--max-model-len",
        str(scheduler["max_model_len"]),
        "--max-num-seqs",
        str(scheduler["max_num_seqs"]),
        "--max-num-batched-tokens",
        str(scheduler["max_num_batched_tokens"]),
        "--max-cudagraph-capture-size",
        str(scheduler["cuda_graph_max_bs"]),
        "--gpu-memory-utilization",
        str(base.get("gpu_memory_utilization", 0.9)),
        "--enable-chunked-prefill",
        "--disable-uvicorn-access-log",
        "--model-loader-extra-config",
        '{"enable_multithread_load":true,"num_threads":128}',
    ]
    if topology["dp"] > 1:
        args.extend(["--data-parallel-size", str(topology["dp"])])
    if topology.get("expert_parallel"):
        args.append("--enable-expert-parallel")

    if features.get("prefix_caching", True):
        args.extend(["--enable-prefix-caching", "--prefix-caching-hash-algo", "sha256"])
    else:
        # vLLM enables prefix caching by default.
        args.append("--no-enable-prefix-caching")
    if features.get("bounded_replay", False):
        args.append("--swa-bounded-replay")
    else:
        args.append("--no-swa-bounded-replay")

    engram = {"cpu_offload": bool(features.get("engram_host", True))}
    if topology["dp"] > 1 and topology.get("expert_parallel"):
        engram["embedding_across_dp"] = True
    args.extend(["--engram-config", json.dumps(engram, separators=(",", ":"))])

    if hardware == "h200":
        args.extend(["--kv-cache-dtype", "fp8", "--block-size", "64"])
    else:
        if topology.get("expert_parallel"):
            attention = {
                "backend": "FLASHMLA_MEGA_ATTN_DSV41",
                "indexer_kv_dtype": "mxfp4",
                "indexer_sparse_logits": True,
            }
            kernel = {
                "enable_flashinfer_autotune": True,
                "moe_backend": (
                    "flashinfer_moe_ep_cutedsl"
                    if is_nvfp4
                    else "deep_gemm_mega_moe"
                ),
            }
        else:
            attention = {
                "backend": "FLASHINFER_MLA_SPARSE_DSV41",
                "indexer_kv_dtype": "mxfp4",
                "indexer_sparse_logits": True,
            }
            kernel = {"enable_flashinfer_autotune": True}
        args.extend(
            [
                "--attention-config",
                json.dumps(attention, separators=(",", ":")),
                "--kernel-config",
                json.dumps(kernel, separators=(",", ":")),
                "--kv-cache-dtype",
                "fp8",
            ]
        )

    if features.get("dspark", False):
        speculation = {
            "method": "dspark",
            "num_speculative_tokens": int(
                features.get("dspark_num_speculative_tokens", 5)
            ),
            "draft_sample_method": "probabilistic",
            "rejection_sample_method": "block",
            "enable_adaptive_verification": bool(
                features.get(
                    "dspark_adaptive_verification",
                    base.get("adaptive_verification", True),
                )
            ),
        }
        args.extend(
            ["--speculative-config", json.dumps(speculation, separators=(",", ":"))]
        )

    args.extend(str(value) for value in profile.get("extra_args") or [])
    args.extend(experiment_args)
    env = {
        "VLLM_ENGINE_READY_TIMEOUT_S": "7200",
        "VLLM_USE_V2_MODEL_RUNNER": "1",
        "VLLM_USE_RUST_FRONTEND": "0",
        "OMP_NUM_THREADS": "1",
    }
    return args, env


def sglang_args(
    hardware: str,
    base: dict[str, Any],
    profile: dict[str, Any],
    port: int,
    experiment_args: list[str],
) -> tuple[list[str], dict[str, str]]:
    topology = profile["topology"]
    scheduler = profile["scheduler"]
    features = profile.get("features") or {}
    args = [
        "serve",
        "--model-path",
        os.environ["MODEL"],
        "--revision",
        os.environ["MODEL_REVISION"],
        "--served-model-name",
        os.environ["SERVED_MODEL"],
        "--trust-remote-code",
        "--host",
        "0.0.0.0",
        "--port",
        str(port),
        "--tp",
        str(topology["tp"]),
        "--ep-size",
        str(topology["ep"]),
        "--context-length",
        str(scheduler["max_model_len"]),
        "--max-running-requests",
        str(scheduler["max_num_seqs"]),
        "--chunked-prefill-size",
        str(scheduler.get("chunked_prefill_size", 4096)),
        "--max-prefill-tokens",
        str(scheduler.get("max_prefill_tokens", 8192)),
        "--cuda-graph-max-bs-decode",
        str(scheduler["cuda_graph_max_bs"]),
        "--reasoning-parser",
        "auto",
        "--tool-call-parser",
        "auto",
        "--watchdog-timeout",
        "3600",
        "--enable-metrics",
    ]
    if "mem_fraction_static" in base:
        args.extend(["--mem-fraction-static", str(base["mem_fraction_static"])])
    if hardware == "h200":
        args.extend(
            [
                "--attention-backend",
                "dsv4",
                "--moe-runner-backend",
                str(base.get("moe_runner_backend", "flashinfer_mxfp4")),
            ]
        )
    if features.get("dspark", False):
        args.extend(
            [
                "--speculative-algorithm",
                "DSPARK",
                "--speculative-dspark-block-size",
                "5",
            ]
        )
    if features.get("bounded_replay", False):
        args.append("--enable-decoder-swa-bounded-replay")
    if features.get("hicache", False):
        args.extend(
            [
                "--enable-hierarchical-cache",
                "--hicache-ratio",
                "2",
                "--hicache-write-policy",
                "write_through",
            ]
        )
    args.extend(str(value) for value in profile.get("extra_args") or [])
    args.extend(experiment_args)

    env = {"PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}
    if features.get("engram_host", False):
        env["SGLANG_ENABLE_DSV41_ENGRAM_HOST_TABLE"] = "1"
        env["SGLANG_DSV41_ENGRAM_HOST_TABLE_LAYOUT"] = str(
            base.get("engram_host_layout", "per_rank")
        )
    return args, env


def wait_ready(
    url: str,
    processes: list[subprocess.Popen[Any]],
    timeout_s: int = 7200,
) -> None:
    deadline = time.monotonic() + timeout_s
    last_error = ""
    while time.monotonic() < deadline:
        for process in processes:
            exit_code = process.poll()
            if exit_code is not None:
                raise RuntimeError(
                    f"server process {process.pid} exited before readiness "
                    f"with status {exit_code}"
                )
        try:
            with urllib.request.urlopen(f"{url}/v1/models", timeout=5) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as exc:
            last_error = str(exc)
        time.sleep(5)
    raise RuntimeError(f"server not ready at {url}: {last_error}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hardware", choices=["h200", "b200"], required=True)
    parser.add_argument("--engine", choices=["vllm", "sglang", "tensorrt"], required=True)
    parser.add_argument("--profile", default=os.environ.get("PROFILE", "balanced"))
    parser.add_argument("--experiment", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--stop", action="store_true")
    parser.add_argument("--nsys-output")
    args = parser.parse_args()

    engine_root = ROOT / "serving" / args.hardware / args.engine
    base = load_yaml(engine_root / "base.yaml")
    images = load_yaml(engine_root / "images.yaml")
    profile = load_yaml(engine_root / "profiles" / f"{args.profile}.yaml")
    validate_profile(profile)
    experiment_args, experiment_env = selected_experiments(
        engine_root / "experiments.yaml", args.experiment, args.profile
    )

    if args.validate:
        print(f"validated {args.hardware}/{args.engine}/{args.profile}")
        return

    names = [
        f"dsv41-{args.hardware}-{args.engine}-{args.profile}-{index}"
        for index in range(len(profile["replicas"]))
    ]
    if args.stop:
        subprocess.run(["docker", "rm", "-f", *names], check=False)
        return
    if not args.dry_run and os.environ.get("SKIP_PREFLIGHT", "0") != "1":
        subprocess.run(
            ["bash", str(ROOT / "ops/preflight.sh"), args.hardware], check=True
        )

    image = image_for(args.engine, images)
    commands: list[list[str]] = []
    backends: list[str] = []
    for index, replica in enumerate(profile["replicas"]):
        gpu_ids = str(replica["gpu_ids"])
        if csv_count(gpu_ids) != profile["topology"]["tp"] * profile["topology"]["dp"]:
            raise SystemExit(
                f"replica {index}: GPU count does not match TP×DP topology"
            )
        port = int(replica["port"])
        if args.engine == "vllm":
            engine_args, engine_env = vllm_args(
                args.hardware, base, profile, port, experiment_args
            )
        elif args.engine == "sglang":
            engine_args, engine_env = sglang_args(
                args.hardware, base, profile, port, experiment_args
            )
        else:
            raise SystemExit("TensorRT uses its dedicated experimental launcher")
        engine_args.extend(
            str(value) for value in replica.get("extra_args") or []
        )
        engine_env.update(experiment_env)
        commands.append(
            common_docker(
                name=names[index],
                gpu_ids=gpu_ids,
                image=image,
                engine=args.engine,
                extra_env=engine_env,
                engine_args=engine_args,
                nsys_output=args.nsys_output,
            )
        )
        backends.append(f"http://127.0.0.1:{port}")

    router_command = [
        str(ROOT / ".venv/bin/python"),
        str(ROOT / "lib/router.py"),
        "--port",
        os.environ.get("PORT", "8000"),
        "--backends",
        *backends,
    ]
    if len(backends) > 1:
        try:
            public_port = int(os.environ.get("PORT", "8000"))
        except ValueError as exc:
            raise SystemExit("PORT must be an integer") from exc
        backend_ports = {int(replica["port"]) for replica in profile["replicas"]}
        if public_port in backend_ports:
            raise SystemExit(
                f"router port {public_port} collides with a backend port"
            )
    if args.dry_run:
        for command in commands:
            print(shlex.join(command))
        if len(commands) > 1:
            print(shlex.join(router_command))
        return

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
        for command in commands:
            processes.append(subprocess.Popen(command))
        for backend in backends:
            wait_ready(backend, processes)
        if len(commands) > 1:
            processes.append(subprocess.Popen(router_command))
        exit_code = 0
        while True:
            for process in processes:
                value = process.poll()
                if value is not None:
                    exit_code = value
                    raise SystemExit(exit_code)
            time.sleep(2)
    finally:
        stop_all()


if __name__ == "__main__":
    main()
