from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "infra/mirror_qwen_to_nvme.py"
SPEC = importlib.util.spec_from_file_location("mirror_qwen_to_nvme", SCRIPT)
assert SPEC and SPEC.loader
mirror = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mirror)


def test_pinned_tree_matches_revision_files_without_copying():
    files, digest = mirror.pinned_tree()
    assert len(files) == 32
    assert len([name for name in files if name.endswith(".safetensors")]) == 18
    assert sum(item["size"] for item in files.values()) == 55_586_114_863
    assert len(digest) == 64


def test_git_blob_and_lfs_hash_checks_are_distinct(tmp_path: Path):
    path = tmp_path / "model-file"
    data = b"pinned model bytes"
    path.write_bytes(data)
    blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
    digest = hashlib.sha256(data).hexdigest()
    normal = {"size": len(data), "blob_id": blob}
    assert mirror.assert_file(path, normal) == digest
    # In a Git LFS tree, blob_id hashes the pointer, not the downloaded file.
    lfs = {"size": len(data), "blob_id": "0" * 40, "lfs_sha256": digest}
    assert mirror.assert_file(path, lfs) == digest
    path.write_bytes(b"corrupted bytes!!!")
    with pytest.raises(mirror.MirrorError):
        mirror.assert_file(path, lfs)
