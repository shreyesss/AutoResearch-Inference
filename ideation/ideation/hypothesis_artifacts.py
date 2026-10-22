"""Portable, hash-verified projections for hypothesis test artifacts.

These helpers never rewrite immutable evidence or search the filesystem by name.
Only an explicit state-relative path or an unambiguous legacy research/records
suffix can relocate a record. External files are not implicitly retained.
"""
import hashlib
import re
from pathlib import Path, PurePosixPath


def state_root(memory_path):
    parent = Path(memory_path).resolve().parent
    return parent.parent if parent.name == "research" else parent


def artifact_reference(root, path):
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("A readable test artifact file is required")
    record = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    try:
        relative = path.relative_to(Path(root).resolve())
    except ValueError:
        return record  # Explicit external reference; no retention is promised.
    return {**record, "path": relative.as_posix(), "path_base": "state"}


def resolve_artifact(root, record):
    """Return a read-time projection, never an edited historical record."""
    result = {"original_reference": dict(record), "sha256": record.get("sha256")}
    root = Path(root).resolve()
    raw = record.get("path")
    if not isinstance(raw, str) or not raw or "\\" in raw:
        return {**result, "resolution_status": "invalid_path"}
    path = PurePosixPath(raw)
    if ".." in path.parts or not re.fullmatch(r"[a-f0-9]{64}", str(record.get("sha256", ""))):
        return {**result, "resolution_status": "invalid_reference"}
    if record.get("path_base") == "state":
        if path.is_absolute():
            return {**result, "resolution_status": "invalid_path"}
        relative = path
        method = "state_relative"
    elif record.get("path_base") is not None:
        return {**result, "resolution_status": "invalid_path_base"}
    elif path.is_absolute():
        try:
            relative = Path(raw).relative_to(root)
            method = "legacy_current_root"
        except ValueError:
            # No basename matching, arbitrary old-root probing, or global search.
            offsets = [i for i in range(len(path.parts)-1)
                       if path.parts[i:i+2] == ("research", "records")]
            if len(offsets) != 1 or offsets[0]+2 >= len(path.parts):
                return {**result, "resolution_status": "external_not_retained"}
            relative = PurePosixPath(*path.parts[offsets[0]:])
            method = "legacy_records_suffix"
    else:
        return {**result, "resolution_status": "unbased_relative_path"}
    try:
        candidate = (root / relative).resolve()
    except (OSError, RuntimeError):
        return {**result, "resolution_status": "invalid_path"}
    try:
        candidate.relative_to(root)
    except ValueError:
        return {**result, "resolution_status": "outside_state_root"}
    result.update(state_relative_path=relative.as_posix(), resolution_method=method)
    try:
        if not candidate.is_file():
            return {**result, "resolution_status": "missing"}
        if "bytes" in record and (type(record["bytes"]) is not int or record["bytes"] < 0 or candidate.stat().st_size != record["bytes"]):
            return {**result, "resolution_status": "size_mismatch"}
        if hashlib.sha256(candidate.read_bytes()).hexdigest() != record["sha256"]:
            return {**result, "resolution_status": "hash_mismatch"}
    except OSError:
        return {**result, "resolution_status": "unreadable"}
    return {**result, "resolution_status": "verified", "resolved_local_file": str(candidate)}
