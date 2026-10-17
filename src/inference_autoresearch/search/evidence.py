"""Read-only, allowlisted source snapshots supplied to the proposal context."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_SOURCES = {
    "methods-decisions-v02": "inference-autoresearch-handoff/DECISIONS.md",
    "methods-interfaces-v02": "inference-autoresearch-handoff/docs/INTERFACES.md",
    "methods-implementation-v02": "inference-autoresearch-handoff/docs/IMPLEMENTATION.md",
    "methods-acceptance-v02": "inference-autoresearch-handoff/ACCEPTANCE.md",
    "measured-executive-summary": "EXECUTIVE_SUMMARY.md",
    "measured-b0-calibration": "infra/B0_LOAD_CALIBRATION.md",
    "measured-cap-sensitivity": "infra/SEQUENCE_CAP_SENSITIVITY_PILOT.md",
    "measured-manual-search": "infra/MANUAL_SERVING_SEARCH.md",
    "measured-manual-cells": "infra/manual-serving-search-results.json",
    "capability-spike": "infra/CAPABILITY_SPIKE.md",
    "dataset-qualification": "infra/DATASET_QUALIFICATION.md",
    "campaign-lock-source": "configs/campaign.json",
    "active-domain-source": "configs/search-domain.json",
    "card-short-chat": "configs/workloads/short-chat-card.json",
    "card-mixed-diagnostic": "configs/workloads/mixed-prefill-card.json",
    "card-tracelab-control": "configs/workloads/tracelab-card.json",
}


class EvidenceStore:
    def __init__(self, repo_root: Path, snapshot_root: Path,
                 sources: dict[str, str] | None = None):
        self.repo_root = Path(repo_root).resolve()
        self.snapshot_root = Path(snapshot_root)
        self.sources = sources or DEFAULT_SOURCES

    def snapshot(self) -> list[dict[str, Any]]:
        self.snapshot_root.mkdir(parents=True, exist_ok=True)
        refs = []
        for evidence_id, relative in self.sources.items():
            source = (self.repo_root / relative).resolve()
            if not source.is_relative_to(self.repo_root):
                raise ValueError("evidence path escapes repository")
            if not source.is_file():
                continue
            content = source.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            target = self.snapshot_root / f"{evidence_id}-{digest[:12]}{source.suffix}"
            if target.exists() and target.read_bytes() != content:
                raise ValueError("evidence snapshot collision")
            target.write_bytes(content)
            refs.append({"evidence_id": evidence_id, "source": relative, "sha256": digest,
                         "snapshot_path": str(target), "bytes": len(content), "type": "methods" if
                         evidence_id.startswith("methods") else "measurement"})
        (self.snapshot_root / "manifest.json").write_text(json.dumps(refs, indent=2) + "\n")
        return refs

    def read(self, ref: dict[str, Any], max_bytes: int = 16000) -> bytes:
        if ref.get("evidence_id") not in self.sources:
            raise ValueError("evidence ID not allowlisted")
        path = Path(ref["snapshot_path"]).resolve()
        if not path.is_relative_to(self.snapshot_root.resolve()):
            raise ValueError("evidence path outside snapshot root")
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != ref["sha256"]:
            raise ValueError("evidence snapshot changed")
        return content[:max_bytes]
