"""Trusted single-GPU controller for the pinned Qwen/vLLM server."""

from __future__ import annotations

import fcntl
import json
import os
import re
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from inference_autoresearch.contracts import ResolvedServeConfig, ServerHandle
from inference_autoresearch.runtime.config import PINNED_IMAGE, PinnedEnvironment, verify_model_files


class RuntimeFailure(RuntimeError):
    pass


def _run(args: list[str], *, timeout: float = 30, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if check and result.returncode:
        raise RuntimeFailure(f"{' '.join(args[:3])} exited {result.returncode}: {result.stderr[-2000:]}")
    return result


def _atomic_json(path: Path, payload: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


class _Sampler:
    def __init__(self, url: str, path: Path, period_s: float = 5.0):
        self.url, self.path, self.period_s = url, path, period_s
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._loop, name="iar-telemetry", daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=10)

    def _loop(self) -> None:
        with self.path.open("a") as stream:
            while not self.stop_event.is_set():
                row: dict[str, Any] = {"unix_ns": time.time_ns(), "sample_period_s": self.period_s}
                gpu = _run(["nvidia-smi", "--query-gpu=uuid,utilization.gpu,memory.used,memory.total,power.draw,temperature.gpu",
                            "--format=csv,noheader,nounits"], timeout=10, check=False)
                row["gpu"] = gpu.stdout.strip() if gpu.returncode == 0 else None
                row["gpu_error"] = gpu.stderr.strip() if gpu.returncode else None
                try:
                    with urllib.request.urlopen(self.url + "/metrics", timeout=3) as response:
                        payload = response.read(5_000_000)
                    metrics_path = self.path.parent / f"server-metrics-{row['unix_ns']}.prom"
                    metrics_path.write_bytes(payload)
                    row["server_metrics_path"] = str(metrics_path)
                except (OSError, urllib.error.URLError) as exc:
                    row["server_metrics_error"] = str(exc)
                stream.write(json.dumps(row, sort_keys=True) + "\n")
                stream.flush()
                self.stop_event.wait(self.period_s)


class DockerRuntimeManager:
    """Starts exactly one pinned server and owns its cross-process GPU lease.

    Docker is a trusted evaluator dependency. Proposals never provide image,
    volume, environment, command or host port fields.
    """

    def __init__(self, pinned: PinnedEnvironment, lock_path: Path, *, port: int = 8000,
                 startup_timeout_s: float = 900.0, sample_period_s: float = 5.0):
        self.pinned = pinned
        self.lock_path = lock_path
        self.port = port
        self.startup_timeout_s = startup_timeout_s
        self.sample_period_s = sample_period_s
        self._lease: Any = None
        self._handle: ServerHandle | None = None
        self._sampler: _Sampler | None = None

    def inspect_hardware(self) -> dict[str, Any]:
        gpu = _run(["nvidia-smi", "--query-gpu=uuid,name,memory.total,memory.free,compute_cap,driver_version",
                    "--format=csv,noheader,nounits"])
        rows = [line.strip() for line in gpu.stdout.splitlines() if line.strip()]
        docker = _run(["docker", "version", "--format", "{{.Server.Version}}"])
        image = _run(["docker", "image", "inspect", PINNED_IMAGE, "--format", "{{json .RepoDigests}}"])
        if len(rows) != 1:
            raise RuntimeFailure(f"campaign requires exactly one visible GPU, found {len(rows)}")
        if rows[0].split(",")[0].strip() != self.pinned.gpu_uuid:
            raise RuntimeFailure("visible GPU UUID differs from campaign pin")
        return {"gpu": rows[0], "docker_version": docker.stdout.strip(),
                "image_repo_digests": json.loads(image.stdout), "model_files": verify_model_files(self.pinned.model_dir)}

    def _acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        lease = self.lock_path.open("a+")
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            lease.close()
            raise RuntimeFailure("GPU lease is held by another evaluator") from exc
        lease.seek(0)
        lease.truncate()
        lease.write(json.dumps({"pid": os.getpid(), "acquired_utc_ns": time.time_ns()}) + "\n")
        lease.flush()
        self._lease = lease

    def _release(self) -> None:
        if self._lease is not None:
            fcntl.flock(self._lease.fileno(), fcntl.LOCK_UN)
            self._lease.close()
            self._lease = None

    def start(self, config: ResolvedServeConfig, output_dir: Path) -> ServerHandle:
        if self._handle is not None:
            raise RuntimeFailure("manager already owns a server")
        if config.image_digest != PINNED_IMAGE or config.env:
            raise RuntimeFailure("untrusted image or environment in resolved config")
        if not config.argv or config.argv[0] != "/models/Qwen3.8-27B":
            raise RuntimeFailure("resolved argv must start with the pinned model path")
        # resolve_config is the authority; validate argv and settings again here
        # against its canonical output to prevent manually constructed DTO bypass.
        from inference_autoresearch.runtime.config import resolve_config
        canonical = resolve_config(config.effective_settings, self.pinned)
        if tuple(config.argv) != tuple(canonical.argv) or config.config_id != canonical.config_id:
            raise RuntimeFailure("serve argv/config ID do not match the allowlisted resolver")
        if output_dir.exists() and any(output_dir.iterdir()):
            raise RuntimeFailure(f"server output directory is not empty: {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)
        self._acquire()
        container_name = "iar-" + uuid.uuid4().hex[:12]
        url = f"http://127.0.0.1:{self.port}"
        try:
            hardware = self.inspect_hardware()
            compute = _run(["nvidia-smi", "--query-compute-apps=pid,gpu_uuid",
                            "--format=csv,noheader,nounits"], check=False)
            if compute.returncode:
                raise RuntimeFailure("cannot inspect pre-existing GPU compute processes")
            if compute.stdout.strip():
                raise RuntimeFailure("GPU has pre-existing compute processes; inspect before starting")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                if probe.connect_ex(("127.0.0.1", self.port)) == 0:
                    raise RuntimeFailure(f"port {self.port} is already in use")
            _atomic_json(output_dir / "hardware.json", hardware)
            _atomic_json(output_dir / "requested-config.json", {
                "config_id": config.config_id, "argv": config.argv, "effective_settings": config.effective_settings,
                "model_pins": config.model_pins, "image": config.image_digest,
            })
            # A unique name and localhost-only port keep unrelated workloads out.
            command = ["docker", "run", "--pull", "never", "-d", "--name", container_name,
                       "--label", "inference-autoresearch=server", "--gpus", "all", "--ipc=host",
                       "-p", f"127.0.0.1:{self.port}:8000",
                       "-v", f"{self.pinned.model_dir}:/models/Qwen3.8-27B:ro",
                       PINNED_IMAGE, *config.argv]
            container_id = _run(command, timeout=60).stdout.strip()
            (output_dir / "container-id.txt").write_text(container_id + "\n")
            deadline = time.monotonic() + self.startup_timeout_s
            ready = False
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(url + "/health", timeout=3) as response:
                        ready = response.status == 200
                    if ready:
                        break
                except (OSError, urllib.error.URLError):
                    pass
                state = _run(["docker", "inspect", container_name, "--format", "{{.State.Running}}"], check=False)
                if state.returncode or state.stdout.strip() != "true":
                    raise RuntimeFailure("server exited before readiness")
                time.sleep(5)
            if not ready:
                raise RuntimeFailure("server readiness timed out")
            log_result = _run(["docker", "logs", container_name], check=False)
            log = log_result.stdout + log_result.stderr
            (output_dir / "startup.log").write_text(log)
            evidence = self._verify_startup(log, config)
            _atomic_json(output_dir / "resolved-startup.json", evidence)
            handle = ServerHandle(container_id, url, config.config_id,
                                  {"container_name": container_name, "output_dir": str(output_dir),
                                   "lease_path": str(self.lock_path), "startup_evidence": evidence})
            self._handle = handle
            self._sampler = _Sampler(url, output_dir / "telemetry.jsonl", self.sample_period_s)
            self._sampler.start()
            return handle
        except Exception:
            self._cleanup_container(container_name, output_dir)
            self._release()
            raise

    @staticmethod
    def _verify_startup(log: str, config: ResolvedServeConfig) -> dict[str, Any]:
        expected = config.effective_settings
        checks = {
            "engine_version": "v0.28.0" in log,
            "model_path": "model='/models/Qwen3.8-27B'" in log,
            "max_model_len": "max_seq_len=40960" in log,
            "sequence_cap": f"'max_num_seqs': {expected['max_num_seqs']}" in log,
            "prefix_caching": f"enable_prefix_caching={expected['enable_prefix_caching']}" in log,
            "chunked_prefill": f"enable_chunked_prefill={expected['enable_chunked_prefill']}" in log,
            "token_budget": f"max_num_batched_tokens={expected['max_num_batched_tokens']}" in log,
            "memory_fraction": bool(re.search(r"Desired GPU memory utilization is \(" + re.escape(str(expected["gpu_memory_utilization"])) + r"[,)]", log)),
        }
        if expected["long_prefill_token_threshold"]:
            checks["long_prefill_token_threshold"] = (
                f"'long_prefill_token_threshold': {expected['long_prefill_token_threshold']}" in log
            )
        if expected["mtp_draft_tokens"]:
            checks["mtp"] = f"'num_speculative_tokens': {expected['mtp_draft_tokens']}" in log or f"num_speculative_tokens={expected['mtp_draft_tokens']}" in log
        else:
            checks["mtp"] = "speculative_config=None" in log
        if not all(checks.values()):
            raise RuntimeFailure(f"startup log did not confirm effective config: {checks}")
        return {"checks": checks, "log_excerpt": "startup.log", "verified_utc_ns": time.time_ns()}

    @staticmethod
    def _cleanup_container(name: str, output_dir: Path) -> None:
        state = _run(["docker", "inspect", name, "--format", "{{json .State}}"], check=False)
        if state.returncode == 0:
            (output_dir / "container-state-before-stop.json").write_text(state.stdout)
            _run(["docker", "stop", "--time", "20", name], timeout=40, check=False)
            logs = _run(["docker", "logs", name], check=False)
            (output_dir / "server.log").write_text(logs.stdout + logs.stderr)
            after = _run(["docker", "inspect", name, "--format", "{{json .State}}"], check=False)
            (output_dir / "container-state-after-stop.json").write_text(after.stdout)
            _run(["docker", "rm", name], check=False)

    def stop(self, handle: ServerHandle) -> None:
        if self._handle is None or handle.server_id != self._handle.server_id:
            raise RuntimeFailure("server handle does not belong to this manager")
        if self._sampler is not None:
            self._sampler.stop()
            self._sampler = None
        try:
            self._cleanup_container(handle.metadata["container_name"], Path(handle.metadata["output_dir"]))
        finally:
            self._handle = None
            self._release()
