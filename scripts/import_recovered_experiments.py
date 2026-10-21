#!/usr/bin/env python3
"""Import precisely mapped retained C24/C25 outcomes. Default: verify and preview."""
import argparse
import hashlib
import json
from pathlib import Path

from ideation.experiments import ExperimentRegistry


MAPPINGS = (
    ("memory-component-and-short-results.json", "component", "recovered-C25-component-002", "component", "validated", "C25"),
    ("memory-component-and-short-results.json", "short_probe", "recovered-C24-short-probe", "component", "inconclusive", "C24"),
    ("memory-native-003-result.json", None, "recovered-C25-native-003", "native", "error", "C25"),
)


def records(source):
    source = Path(source).expanduser().resolve(strict=True)
    result = []
    for filename, key, identity, scope, verdict, family in MAPPINGS:
        receipt_path = source / filename
        receipt_raw = receipt_path.read_bytes()
        receipt = json.loads(receipt_raw)
        event = receipt[key] if key else receipt
        data = event["data"]
        if event["type"] != "test_result" or data["verdict"] != verdict or data["scope"]["family"] != family:
            raise ValueError("Unexpected retained receipt disposition: " + filename)
        original_artifact = data["artifact"]
        # Only known artifacts in this frozen run's evaluator directory are read.
        local_artifact = (source / "evaluator" / Path(original_artifact["path"]).name).resolve(strict=True)
        if source not in local_artifact.parents:
            raise ValueError("Artifact escapes source run")
        raw = local_artifact.read_bytes()
        if hashlib.sha256(raw).hexdigest() != original_artifact["sha256"] or len(raw) != original_artifact["bytes"]:
            raise ValueError("Retained artifact checksum/size mismatch: " + local_artifact.name)
        baseline_evidence = {field: data["scope"][field] for field in ("image", "hardware")}
        baseline_id = "baseline:" + hashlib.sha256(json.dumps(baseline_evidence, sort_keys=True).encode()).hexdigest()
        result.append({
            "experiment_id": identity, "hypothesis_id": event["hypothesis_id"],
            "baseline_id": baseline_id, "scope": scope, "status": verdict,
            "original_event_id": event["id"], "original_at": event["at"],
            "note": data["note"], "artifacts": [str(local_artifact), str(receipt_path)],
            "provenance": {"source_run": source.name, "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest(),
                           "receipt_key": key, "original_test_id": data["test_id"],
                           "original_artifact": original_artifact, "retained_scope": data["scope"],
                           "baseline_evidence": baseline_evidence,
                           "baseline_limit": "Identity derived from retained image/hardware only; not a complete runtime reattestation",
                           "import_mode": "Explicit historical receipt; no new measurements or promotion"},
        })
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="Recovered h200-overnight-001 run directory")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--apply", action="store_true", help="Append verified historical receipts; otherwise dry-run")
    args = parser.parse_args(argv)
    items = records(args.source)  # Verify every input before opening mutable state.
    if args.apply:
        registry = ExperimentRegistry(args.state_dir)
        try:
            outcomes = [registry.import_historical(**item) for item in items]
        finally:
            registry.close()
    else:
        outcomes = items
    print(json.dumps({"mode": "applied" if args.apply else "dry_run", "experiments": outcomes,
                      "C26": "Not imported as measured component/native/service outcome; source applicability rejection remains in APPLICABILITY_REVIEW.md",
                      "new_gpu_experiments": 0}, indent=2))


if __name__ == "__main__":
    main()
