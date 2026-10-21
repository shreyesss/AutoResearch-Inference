"""Independent, append-only experiment registry.

An experiment is one attempt at one immutable scope and baseline. A component
result never changes the status of a native/service attempt. Verdicts record
operator assertions; checksums establish artifact identity, not scientific truth.
"""
import hashlib
import json
import math
import os
import re
import sqlite3
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote


STATES = {"proposed", "accepted", "rejected", "planned", "running", "validated",
          "invalidated", "inconclusive", "error"}
SCOPES = {"component", "native", "service"}
ARTIFACT_LIMIT = 16 * 1024 * 1024
ARTIFACT_EXTENSIONS = {".json", ".jsonl", ".md", ".csv", ".txt", ".yaml", ".yml"}
TRANSITIONS = {
    "proposed": {"accepted", "rejected"},
    "accepted": {"planned", "rejected"},
    "planned": {"running", "error", "rejected"},
    "running": {"validated", "invalidated", "inconclusive", "error"},
}


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _identity(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,199}", value):
        raise ValueError(name + " must be a simple identifier (no paths)")
    return value


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + " is required")
    return value


def _roi(value):
    if not isinstance(value, dict):
        raise ValueError("ROI must be an explicit estimate, with unknowns if unmeasured")
    for field in ("metric", "unit"):
        _text(value.get(field), "roi." + field)
    for field in ("baseline_value", "expected_relative_gain", "min_relative_gain"):
        if field not in value:
            raise ValueError("Missing roi." + field)
        number = value[field]
        if number is None and field != "min_relative_gain":
            continue
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not math.isfinite(number):
            raise ValueError("roi." + field + " must be finite")
        if field in ("baseline_value", "min_relative_gain") and number < 0:
            raise ValueError("roi." + field + " must be nonnegative")
    if not value.get("assumptions"):
        raise ValueError("ROI assumptions are required")
    if (value["baseline_value"] is None or value["expected_relative_gain"] is None) and not value.get("unknowns"):
        raise ValueError("Unknown ROI quantities require explicit unknowns")
    _json(value)
    return value


def artifact_reference(value):
    """Hash a local file, or retain an explicitly unverified remote reference."""
    if isinstance(value, (str, Path)):
        path = Path(value).expanduser().resolve(strict=True)
        if not path.is_file():
            raise ValueError("Artifact must be a regular file")
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
        return {"uri": path.as_uri(), "sha256": digest.hexdigest(), "bytes": size,
                "verification": "local_content_hashed"}
    if not isinstance(value, dict):
        raise ValueError("Artifact must be a local filename or URI/hash reference")
    uri = _text(value.get("uri"), "artifact.uri")
    digest = value.get("sha256", "")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
        raise ValueError("Artifact requires a SHA-256 digest")
    return {"uri": uri, "sha256": digest.lower(), "verification": "caller_supplied_unverified"}


class ExperimentRegistry:
    def __init__(self, root):
        self.root = Path(root).expanduser().resolve()
        self.directory = self.root / "experiments"
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "experiments.sqlite3"
        self.db = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS experiments (
          id TEXT PRIMARY KEY, snapshot TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS experiment_events (
          seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
          experiment_id TEXT NOT NULL REFERENCES experiments(id),
          at TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS experiment_events_parent ON experiment_events(experiment_id, seq);
        CREATE TABLE IF NOT EXISTS artifact_copies (
          sha256 TEXT PRIMARY KEY, state_relative_path TEXT NOT NULL,
          bytes INTEGER NOT NULL, retained_at TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS artifact_copies_no_update BEFORE UPDATE ON artifact_copies
          BEGIN SELECT RAISE(ABORT, 'artifact index is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS artifact_copies_no_delete BEFORE DELETE ON artifact_copies
          BEGIN SELECT RAISE(ABORT, 'artifact index is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS experiments_no_update BEFORE UPDATE ON experiments
          BEGIN SELECT RAISE(ABORT, 'experiment registry is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS experiments_no_delete BEFORE DELETE ON experiments
          BEGIN SELECT RAISE(ABORT, 'experiment registry is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON experiment_events
          BEGIN SELECT RAISE(ABORT, 'experiment registry is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON experiment_events
          BEGIN SELECT RAISE(ABORT, 'experiment registry is append-only'); END;
        """)

    def close(self):
        self.db.close()

    @contextmanager
    def _transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    @staticmethod
    def _artifact_source(reference):
        parsed = urlparse(reference.get("uri", ""))
        if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
            return None, "external_reference_not_downloaded"
        path = Path(unquote(parsed.path))
        names = {part.lower() for part in path.parts}
        name = path.name.lower()
        if names.intersection({".aws", ".ssh", ".env"}) or name.startswith((".env", "id_rsa", "id_ed25519")) or any(word in name for word in ("credential", "secret", "private_key", "access_key", "api_key", "token")):
            return None, "blocked_sensitive_filename"
        if path.suffix.lower() not in ARTIFACT_EXTENSIONS:
            return None, "unsupported_artifact_type_external_retention_required"
        if reference.get("bytes", 0) > ARTIFACT_LIMIT:
            return None, "exceeds_16MiB_external_retention_required"
        return path, None

    def _resolved_artifact(self, reference):
        digest = reference["sha256"]
        result = {"original_uri": reference["uri"], "sha256": digest}
        row = self.db.execute("SELECT * FROM artifact_copies WHERE sha256=?", (digest,)).fetchone()
        if row:
            relative = Path(row["state_relative_path"])
            target = self.root / relative
            safe = (not relative.is_absolute() and ".." not in relative.parts and
                    target.parent == self.directory / "artifacts" and target.name.startswith(digest + ".") and
                    not target.is_symlink() and not target.parent.is_symlink())
            if not safe:
                return {**result, "retention_status": "invalid_retained_path"}
            result.update(state_relative_path=relative.as_posix(), resolved_local_file=str(target), bytes=row["bytes"])
            if not target.is_file():
                return {**result, "retention_status": "retained_copy_missing"}
            if target.stat().st_size > ARTIFACT_LIMIT or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                return {**result, "retention_status": "retained_copy_hash_mismatch"}
            return {**result, "retention_status": "retained_verified", "verification": "retained_local_content_sha256"}
        path, status = self._artifact_source(reference)
        if status:
            return {**result, "retention_status": status}
        if not path.is_file():
            return {**result, "retention_status": "original_source_unavailable"}
        if path.stat().st_size > ARTIFACT_LIMIT:
            return {**result, "retention_status": "exceeds_16MiB_external_retention_required"}
        return {**result, "retention_status": "eligible_not_retained"}

    def retain_artifacts(self, experiment_id=None):
        """Copy bounded local evidence without altering any original event receipt.

        Remote URIs and large/binary profiles remain explicit external references.
        A retained local hash verifies bytes, never a scientific conclusion.
        """
        if experiment_id is not None:
            _identity(experiment_id, "experiment_id")
            self.get(experiment_id)  # Reject unknown IDs rather than report success.
        where = " WHERE experiment_id=?" if experiment_id is not None else ""
        params = (experiment_id,) if experiment_id is not None else ()
        rows = self.db.execute("SELECT event_id,payload FROM experiment_events" + where + " ORDER BY seq", params).fetchall()
        results = []
        with self._transaction():
            for row in rows:
                for reference in json.loads(row["payload"]).get("artifacts", []):
                    resolved = self._resolved_artifact(reference)
                    if resolved["retention_status"] == "eligible_not_retained":
                        source, _ = self._artifact_source(reference)
                        with source.open("rb") as stream:
                            raw = stream.read(ARTIFACT_LIMIT + 1)
                        if len(raw) > ARTIFACT_LIMIT:
                            resolved["retention_status"] = "exceeds_16MiB_external_retention_required"
                        elif hashlib.sha256(raw).hexdigest() != reference["sha256"]:
                            resolved["retention_status"] = "original_source_hash_mismatch"
                        else:
                            directory = self.directory / "artifacts"
                            if directory.is_symlink():
                                raise ValueError("Artifact retention directory must not be a symlink")
                            directory.mkdir(exist_ok=True)
                            target = directory / (reference["sha256"] + source.suffix.lower())
                            temporary = None
                            try:
                                with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
                                    temporary = Path(stream.name)
                                    stream.write(raw)
                                    stream.flush()
                                    os.fsync(stream.fileno())
                                try:
                                    os.link(temporary, target)
                                except FileExistsError:
                                    if target.is_symlink() or hashlib.sha256(target.read_bytes()).hexdigest() != reference["sha256"]:
                                        raise ValueError("Existing retained artifact content differs")
                            finally:
                                if temporary is not None:
                                    temporary.unlink(missing_ok=True)
                            self.db.execute("INSERT OR IGNORE INTO artifact_copies VALUES(?,?,?,?)",
                                (reference["sha256"], target.relative_to(self.root).as_posix(), len(raw), datetime.now(timezone.utc).isoformat()))
                            resolved = self._resolved_artifact(reference)
                    results.append({"event_id": row["event_id"], **resolved})
        return {"artifacts": results, "retained_verified": sum(row["retention_status"] == "retained_verified" for row in results),
                "event_receipts_modified": False, "max_file_bytes": ARTIFACT_LIMIT}

    @staticmethod
    def _event_id(experiment_id, status, payload, event_id):
        if event_id is not None:
            return _identity(event_id, "event_id")
        return "event:" + hashlib.sha256(_json([experiment_id, status, payload]).encode()).hexdigest()

    def _existing_event(self, event_id, experiment_id, status, payload):
        row = self.db.execute("SELECT * FROM experiment_events WHERE event_id=?", (event_id,)).fetchone()
        if row and (row["experiment_id"] != experiment_id or row["status"] != status or row["payload"] != _json(payload)):
            raise ValueError("Conflicting payload for immutable event_id")
        return row

    def _append(self, event_id, experiment_id, status, payload):
        at = datetime.now(timezone.utc).isoformat()
        self.db.execute("INSERT INTO experiment_events(event_id,experiment_id,at,status,payload) VALUES(?,?,?,?,?)",
                        (event_id, experiment_id, at, status, _json(payload)))

    def create(self, experiment_id, hypothesis_id, baseline_id, scope, *, provenance,
               actor="operator", roi=None, evaluation_plan=None, event_id=None):
        for name, value in (("experiment_id", experiment_id), ("hypothesis_id", hypothesis_id), ("baseline_id", baseline_id)):
            _identity(value, name)
        if scope not in SCOPES:
            raise ValueError("scope must be component, native, or service")
        if not isinstance(provenance, dict) or not provenance:
            raise ValueError("Nonempty provenance required (source/run/code/hardware references)")
        _text(actor, "actor")
        if roi is not None:
            _roi(roi)
        if evaluation_plan is not None and (not isinstance(evaluation_plan, dict) or not evaluation_plan):
            raise ValueError("evaluation_plan must be a nonempty object")
        snapshot = {"id": experiment_id, "hypothesis_id": hypothesis_id, "baseline_id": baseline_id,
                    "scope": scope, "provenance": provenance, "roi": roi, "evaluation_plan": evaluation_plan}
        payload = {"actor": actor, "snapshot": snapshot}
        event_id = self._event_id(experiment_id, "proposed", payload, event_id)
        with self._transaction():
            if not self._existing_event(event_id, experiment_id, "proposed", payload):
                row = self.db.execute("SELECT snapshot FROM experiments WHERE id=?", (experiment_id,)).fetchone()
                if row:
                    raise ValueError("Experiment already exists; reuse original event_id or create a new attempt")
                self.db.execute("INSERT INTO experiments VALUES(?,?,?)", (experiment_id, _json(snapshot), datetime.now(timezone.utc).isoformat()))
                self._append(event_id, experiment_id, "proposed", payload)
        return self.get(experiment_id)

    def import_historical(self, experiment_id, hypothesis_id, baseline_id, scope, *,
                          status, provenance, artifacts, note, original_event_id,
                          original_at, actor="historical-import"):
        """Import an attested final event without fabricating intermediate states.

        The caller must verify the source receipt; no historical ROI or execution
        is inferred. Original event identity/time remain separate from import time.
        """
        for name, value in (("experiment_id", experiment_id), ("hypothesis_id", hypothesis_id),
                            ("baseline_id", baseline_id), ("original_event_id", original_event_id)):
            _identity(value, name)
        if scope not in SCOPES:
            raise ValueError("Unknown historical scope")
        if status not in {"validated", "invalidated", "inconclusive", "error", "rejected"}:
            raise ValueError("Historical import requires an explicit final disposition")
        if not isinstance(provenance, dict) or not provenance:
            raise ValueError("Historical provenance required")
        _text(note, "note")
        _text(actor, "actor")
        _text(original_at, "original_at")
        timestamp = datetime.fromisoformat(original_at.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("Historical timestamp must include timezone")
        refs = [artifact_reference(value) for value in artifacts]
        if not refs:
            raise ValueError("Historical imports require retained evidence artifacts")
        snapshot = {"id": experiment_id, "hypothesis_id": hypothesis_id, "baseline_id": baseline_id,
                    "scope": scope, "provenance": provenance, "roi": None, "evaluation_plan": None}
        payload = {"actor": actor, "note": note, "artifacts": refs, "historical_import": True,
                   "original_event_id": original_event_id, "original_at": original_at,
                   "snapshot": snapshot, "meaning": "Imported retained outcome, not a new execution; intermediate lifecycle and ROI not reconstructed."}
        event_id = "import:" + hashlib.sha256(original_event_id.encode()).hexdigest()
        with self._transaction():
            if not self._existing_event(event_id, experiment_id, status, payload):
                if self.db.execute("SELECT 1 FROM experiments WHERE id=?", (experiment_id,)).fetchone():
                    raise ValueError("Historical import conflicts with existing experiment")
                self.db.execute("INSERT INTO experiments VALUES(?,?,?)", (experiment_id, _json(snapshot), original_at))
                self._append(event_id, experiment_id, status, payload)
        self.retain_artifacts(experiment_id)
        return self.get(experiment_id)

    def transition(self, experiment_id, status, *, note, actor="operator", artifacts=(),
                   metrics=None, event_id=None, expected_status=None, roi=None, evaluation_plan=None):
        _identity(experiment_id, "experiment_id")
        if status not in STATES or status == "proposed":
            raise ValueError("Unknown transition status")
        _text(actor, "actor")
        _text(note, "note")
        refs = [artifact_reference(value) for value in artifacts]
        if status in {"validated", "invalidated"} and not refs:
            raise ValueError("Validated/invalidated outcomes require artifact references")
        if metrics is not None and not isinstance(metrics, dict):
            raise ValueError("metrics must be an object of evaluator-reported measurements")
        if roi is not None:
            _roi(roi)
        if evaluation_plan is not None and (not isinstance(evaluation_plan, dict) or not evaluation_plan):
            raise ValueError("evaluation_plan must be a nonempty object")
        payload = {"actor": actor, "note": note, "artifacts": refs, "metrics": metrics,
                   "roi": roi, "evaluation_plan": evaluation_plan}
        event_id = self._event_id(experiment_id, status, payload, event_id)
        with self._transaction():
            if not self._existing_event(event_id, experiment_id, status, payload):
                current = self.get(experiment_id)
                if expected_status is not None and current["status"] != expected_status:
                    raise ValueError("Stale expected_status; reload experiment before acting")
                if status not in TRANSITIONS.get(current["status"], set()):
                    raise ValueError("Invalid transition %s -> %s; terminal attempts require a new id" % (current["status"], status))
                if status in {"accepted", "planned"}:
                    _roi(roi if roi is not None else current["roi"])
                    plan = evaluation_plan if evaluation_plan is not None else current["evaluation_plan"]
                    if not isinstance(plan, dict) or not plan:
                        raise ValueError("Acceptance/planning requires an evaluation_plan")
                self._append(event_id, experiment_id, status, payload)
        self.retain_artifacts(experiment_id)
        return self.get(experiment_id)

    def get(self, experiment_id):
        _identity(experiment_id, "experiment_id")
        row = self.db.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
        if not row:
            raise KeyError("Unknown experiment: " + experiment_id)
        value = json.loads(row["snapshot"])
        value["created_at"] = row["created_at"]
        value["events"] = []
        for event in self.db.execute("SELECT * FROM experiment_events WHERE experiment_id=? ORDER BY seq", (experiment_id,)):
            item = dict(event)
            item["payload"] = json.loads(item["payload"])
            value["events"].append(item)
            value["status"] = item["status"]
            for field in ("roi", "evaluation_plan"):
                if item["payload"].get(field) is not None:
                    value[field] = item["payload"][field]
        value["resolved_artifacts"] = [{"event_id": event["event_id"], **self._resolved_artifact(reference)}
                                       for event in value["events"] for reference in event["payload"].get("artifacts", [])]
        value["meaning"] = "Evaluator-reported outcome for this baseline and scope only; no automatic cross-scope promotion."
        return value

    def list(self, *, status=None, hypothesis_id=None, baseline_id=None, scope=None):
        if status is not None and status not in STATES:
            raise ValueError("Unknown status")
        if scope is not None and scope not in SCOPES:
            raise ValueError("Unknown scope")
        result = []
        for row in self.db.execute("SELECT id FROM experiments ORDER BY created_at,id").fetchall():
            record = self.get(row["id"])
            if all(wanted is None or record[field] == wanted for field, wanted in
                   (("status", status), ("hypothesis_id", hypothesis_id), ("baseline_id", baseline_id), ("scope", scope))):
                result.append(record)
        return result

    def export(self, path=None):
        """Return a consistent snapshot; optionally atomically write portable JSON.

        SQLite is local to a single node. Publish snapshots to durable storage;
        do not copy a live database file without its WAL or share it over S3.
        """
        self.db.execute("BEGIN")
        try:
            value = {"schema_version": 1, "experiments": self.list()}
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise
        if path is not None:
            target = Path(path).expanduser().resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=str(target.parent), delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(str(temporary), str(target))
            finally:
                if temporary is not None and temporary.exists():
                    temporary.unlink()
        return value
