#!/usr/bin/env python3
"""Future-only verified mirror of the pinned Qwen checkpoint onto local NVMe.

This script does not alter the active model directory, serving runtime or any
campaign. `plan` is read-only. `mirror` requires an idle GPU, streams a copy to
a private staging directory, verifies the pinned Hugging Face tree's LFS SHA-256
or Git blob ID for every source file, rehashes the target, then atomically
promotes it. `verify` rehashes an existing mirror before a future runner uses it.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from inference_autoresearch.runtime.config import PINNED_IMAGE, PINNED_MODEL_REVISION


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".artifacts/models/Qwen3.8-27B"
TREE = SOURCE / ".cache/huggingface/trees" / f"{PINNED_MODEL_REVISION}.json"
NVME = Path("/opt/dlami/nvme")
DESTINATION = NVME / "inference-autoresearch/models" / f"Qwen3.8-27B-{PINNED_MODEL_REVISION}"
RECEIPT = "nvme-mirror-manifest.json"
BUFFER_BYTES = 8 * 1024 * 1024
GPU_LOCK = ROOT / ".artifacts/gpu-9bb5b2a6-b234-55f6-6462-e030fcadfa83.lock"


class MirrorError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BUFFER_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def pinned_tree() -> tuple[dict[str, Any], str]:
    if not TREE.is_file() or TREE.is_symlink():
        raise MirrorError("pinned Hugging Face tree metadata is absent")
    data = json.loads(TREE.read_text())
    files = data.get("files")
    if not isinstance(files, dict) or len(files) != 32:
        raise MirrorError("pinned tree no longer describes 32 checkpoint files")
    actual = {path.name for path in SOURCE.iterdir() if path.is_file()}
    if set(files) != actual or len([name for name in files if name.endswith(".safetensors")]) != 18:
        raise MirrorError("source root files differ from pinned revision tree")
    for name, entry in files.items():
        if (not isinstance(name, str) or name in ("", ".", "..") or "/" in name
                or not isinstance(entry, dict) or type(entry.get("size")) is not int
                or entry["size"] <= 0 or not re.fullmatch(r"[0-9a-f]{40}", entry.get("blob_id", ""))):
            raise MirrorError(f"invalid pinned tree entry: {name!r}")
        source = SOURCE / name
        if source.is_symlink() or not source.is_file() or source.stat().st_size != entry["size"]:
            raise MirrorError(f"source file absent, symlinked or wrong-sized: {name}")
        lfs = entry.get("lfs_sha256")
        if lfs is not None and not re.fullmatch(r"[0-9a-f]{64}", lfs):
            raise MirrorError(f"invalid LFS SHA-256 for {name}")
        if name.endswith(".safetensors") and lfs is None:
            raise MirrorError(f"weight shard lacks independent LFS SHA-256: {name}")
    return files, sha256(TREE)


def nvme_ready() -> dict[str, Any]:
    if not NVME.is_mount() or not NVME.is_dir():
        raise MirrorError("local NVMe is not mounted at /opt/dlami/nvme")
    mount = subprocess.run(["findmnt", "-n", "-o", "SOURCE", "--target", str(NVME)],
                           capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    model = subprocess.run(["lsblk", "-dn", "-o", "MODEL", "/dev/nvme1n1"],
                           capture_output=True, text=True, check=True, timeout=10).stdout.strip()
    if mount != "/dev/mapper/vg.01-lv_ephemeral" or model != "Amazon EC2 NVMe Instance Storage":
        raise MirrorError("destination is not the inspected local instance-store volume")
    if SOURCE.stat().st_dev == NVME.stat().st_dev:
        raise MirrorError("source and destination resolve to the same filesystem")
    return {"mount": mount, "device_model": model,
            "free_bytes": shutil.disk_usage(NVME).free}


def idle_gpu() -> None:
    compute = subprocess.run(["nvidia-smi", "--query-compute-apps=pid",
                              "--format=csv,noheader,nounits"], capture_output=True,
                             text=True, check=True, timeout=15)
    if compute.stdout.strip():
        raise MirrorError("GPU compute is active; refusing to compete with model loading")
    containers = subprocess.run(["docker", "ps", "--format", "{{.Names}}",
                                 "--filter", "label=inference-autoresearch=server"],
                                capture_output=True, text=True, check=True, timeout=15)
    if containers.stdout.strip():
        raise MirrorError("an inference-autoresearch server is running")
    b0 = subprocess.run(["docker", "container", "inspect", "iar-b0"],
                        capture_output=True, check=False, timeout=15)
    if b0.returncode == 0:
        raise MirrorError("shared B0 server exists")


def file_digests(path: Path, size: int) -> tuple[str, str]:
    sha = hashlib.sha256()
    blob = hashlib.sha1(f"blob {size}\0".encode())
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(BUFFER_BYTES), b""):
            sha.update(block)
            blob.update(block)
    return sha.hexdigest(), blob.hexdigest()


def assert_file(path: Path, entry: dict[str, Any], *, expected_sha256: str | None = None) -> str:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != entry["size"]:
        raise MirrorError(f"file missing, symlinked or wrong-sized: {path}")
    digest, blob = file_digests(path, entry["size"])
    if ((entry.get("lfs_sha256") and digest != entry["lfs_sha256"]) or
            (not entry.get("lfs_sha256") and blob != entry["blob_id"]) or
            (expected_sha256 and digest != expected_sha256)):
        raise MirrorError(f"pinned revision digest mismatch: {path}")
    return digest


def verify() -> dict[str, Any]:
    files, tree_sha = pinned_tree()
    nvme_ready()
    receipt_path = DESTINATION / RECEIPT
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise MirrorError("complete NVMe mirror receipt is absent")
    receipt = json.loads(receipt_path.read_text())
    if (receipt.get("schema_version") != "nvme-model-mirror-v1"
            or receipt.get("model_revision") != PINNED_MODEL_REVISION
            or receipt.get("vllm_image_digest") != PINNED_IMAGE
            or receipt.get("source_tree_sha256") != tree_sha
            or set(receipt.get("files", {})) != set(files)):
        raise MirrorError("NVMe mirror receipt differs from pinned model source")
    actual = {path.name for path in DESTINATION.iterdir() if path.is_file()}
    if actual != set(files) | {RECEIPT}:
        raise MirrorError("NVMe mirror contains unexpected or missing root files")
    for name, entry in files.items():
        assert_file(DESTINATION / name, entry,
                    expected_sha256=receipt["files"][name]["sha256"])
    return {"status": "verified", "destination": str(DESTINATION),
            "receipt_sha256": sha256(receipt_path), "source_tree_sha256": tree_sha,
            "file_count": len(files), "total_bytes": sum(x["size"] for x in files.values()),
            "model_revision": PINNED_MODEL_REVISION}


def mirror() -> dict[str, Any]:
    files, tree_sha = pinned_tree()
    volume = nvme_ready()
    total_bytes = sum(entry["size"] for entry in files.values())
    if volume["free_bytes"] < total_bytes + 20 * 1024 ** 3:
        raise MirrorError("NVMe lacks checkpoint bytes plus a 20 GiB reserve")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    with (DESTINATION.parent / ".mirror-qwen.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        GPU_LOCK.parent.mkdir(parents=True, exist_ok=True)
        with GPU_LOCK.open("a+") as gpu_lock:
            fcntl.flock(gpu_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            idle_gpu()
            if DESTINATION.exists():
                return verify() | {"action": "existing_mirror_verified"}
            staging = DESTINATION.parent / f".staging-{PINNED_MODEL_REVISION}-{uuid.uuid4().hex[:8]}"
            staging.mkdir(mode=0o700)
            try:
                hashes: dict[str, dict[str, Any]] = {}
                for name, entry in sorted(files.items()):
                    source, target = SOURCE / name, staging / name
                    before = source.stat()
                    sha = hashlib.sha256()
                    blob = hashlib.sha1(f"blob {entry['size']}\0".encode())
                    with source.open("rb") as inp, target.open("xb") as out:
                        for block in iter(lambda: inp.read(BUFFER_BYTES), b""):
                            out.write(block)
                            sha.update(block)
                            blob.update(block)
                        out.flush()
                        os.fsync(out.fileno())
                    after = source.stat()
                    if (before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns
                            or before.st_ino != after.st_ino
                            or (entry.get("lfs_sha256") and sha.hexdigest() != entry["lfs_sha256"])
                            or (not entry.get("lfs_sha256") and blob.hexdigest() != entry["blob_id"])):
                        raise MirrorError(f"source changed or failed independent revision pin: {name}")
                    digest = assert_file(target, entry, expected_sha256=sha.hexdigest())
                    hashes[name] = {"size": entry["size"], "sha256": digest,
                                    "verification": "lfs_sha256" if entry.get("lfs_sha256")
                                    else "git_blob"}
                receipt = {"schema_version": "nvme-model-mirror-v1",
                           "status": "complete_hash_verified", "model_id": "Qwen/Qwen3.8-27B",
                           "model_revision": PINNED_MODEL_REVISION,
                           "vllm_image_digest": PINNED_IMAGE,
                           "source_root": str(SOURCE), "destination": str(DESTINATION),
                           "source_tree_sha256": tree_sha,
                           "created_at_utc": datetime.now(UTC).isoformat(),
                           "total_bytes": total_bytes, "files": hashes}
                receipt_path = staging / RECEIPT
                with receipt_path.open("x") as stream:
                    json.dump(receipt, stream, indent=2, sort_keys=True)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                # This is the only point at which the future runner can discover it.
                staging.rename(DESTINATION)
                return verify() | {"action": "new_mirror_created"}
            finally:
                if staging.exists():
                    shutil.rmtree(staging)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "mirror", "verify"))
    args = parser.parse_args()
    if args.action == "plan":
        files, tree_sha = pinned_tree()
        print(json.dumps({"status": "planned_no_copy", "source": str(SOURCE),
                          "destination": str(DESTINATION), "volume": nvme_ready(),
                          "model_revision": PINNED_MODEL_REVISION,
                          "source_tree_sha256": tree_sha, "file_count": len(files),
                          "total_bytes": sum(entry["size"] for entry in files.values()),
                          "shards": sum(name.endswith(".safetensors") for name in files)}, indent=2))
    else:
        print(json.dumps(mirror() if args.action == "mirror" else verify(), indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"NVMe mirror blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
