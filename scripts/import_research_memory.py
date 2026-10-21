#!/usr/bin/env python3
"""Recover retained hypothesis records; default dry-run, no fabricated outcomes.

Original exported events remain immutable evidence snapshots. Reconstructed
ledger registration/review events occur at import time and do not replace the
source timestamps. Known IDs are never silently changed to fit a new local path.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
from pathlib import Path

from ideation.hypothesis_memory import HypothesisMemory, digest


PRIOR_ROOTS = (
    "/home/ubuntu/AutoResearch-Inference/ideation/runs",
    "/home/ubuntu/shreyas/skunk-work/ideation/runs",
    "/Users/shreyas/workspace/skunk-work/ideation/runs",
    "/Users/shreyas/Desktop/work/skunk-work/ideation/runs",
)


def collect(roots, original_roots=()):
    artifacts, records, gaps, export_summaries = {}, {}, [], []

    def read(path):
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        artifacts[str(path.resolve())] = {"sha256": sha, "bytes": len(raw), "raw": raw}
        return json.loads(raw)

    paths = []
    for root in roots:
        root = Path(root).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ValueError("Source root must be a run directory")
        for pattern in ("**/*memory*export*.json", "**/history.json", "**/propose-*.json", "**/draft.json", "**/final.json", "**/repair.json", "**/hypotheses.json"):
            paths += [(root, p) for p in root.glob(pattern) if not p.name.endswith(".schema.json")]
    paths = list(dict.fromkeys(paths))
    paths.sort(key=lambda item: ("export" not in item[1].name, str(item[1])))
    for root, path in paths:
        try:
            value = read(path)
            exported = isinstance(value, dict) and isinstance(value.get("hypotheses"), list) and "stats" in value
            if exported:
                entries = value["hypotheses"]
                actual = {"hypotheses": len(entries), "events": sum(len(r.get("events", [])) for r in entries),
                          "tests": sum(len(r.get("tests", [])) for r in entries)}
                export_summaries.append({"path": str(path), "scope": value.get("scope"), "reported_global_stats": value["stats"],
                                         "available_in_this_export": actual,
                                         "not_in_this_export": {k: max(0, value["stats"].get(k, 0) - count) for k, count in actual.items()}})
            elif isinstance(value, list):
                entries = value
            elif isinstance(value, dict) and isinstance(value.get("hypotheses"), list):
                entries = [{"card": card} for card in value["hypotheses"]]
            else:
                gaps.append({"path": str(path), "reason": "unsupported artifact shape retained verbatim"})
                continue
            folder = path.parent
            accompanying = {}
            for name, fallback in (("brief.json", {"legacy": True, "baseline": {"unknown": True}}),
                                   ("rubric.json", {"legacy": True, "policy_unknown": True}), ("sources.json", [])):
                accompanying[name] = read(folder / name) if (folder / name).exists() else fallback
            for entry in entries:
                card = entry.get("card", entry)
                if not isinstance(card, dict) or not card.get("id"):
                    gaps.append({"path": str(path), "reason": "record has no hypothesis card ID"})
                    continue
                known_id = entry.get("id") if exported else entry.get("global_id")
                original_run = entry.get("run") if exported else None
                identity_origin = "original exported run"
                if not original_run:
                    relative = folder.relative_to(root)
                    suffixes = [relative]
                    if path.name != "history.json" and not path.name.startswith("propose-"):
                        suffixes.insert(0, relative / path.stem)
                    candidates = [str(Path(prior) / suffix) for prior in (*original_roots, *PRIOR_ROOTS, str(root)) for suffix in suffixes]
                    candidates += [str(Path(prefix) / suffix) for prefix in ("runs", "ideation/runs") for suffix in suffixes]
                    if known_id:
                        original_run = next((run for run in candidates if HypothesisMemory.identity(run, card["id"]) == known_id), None)
                        identity_origin = "original run recovered by exact ID hash match"
                        if original_run is None:
                            gaps.append({"path": str(path), "id": known_id, "reason": "original run identity unresolved; known ID not regenerated"})
                            continue
                    else:
                        original_run = "legacy-artifact:" + artifacts[str(path.resolve())]["sha256"]
                        identity_origin = "artifact-scoped reconstruction; original run identity unavailable"
                identity = HypothesisMemory.identity(original_run, card["id"])
                if known_id and identity != known_id:
                    gaps.append({"path": str(path), "id": known_id, "reason": "exported ID does not match original run/card ID; snapshot retained"})
                    continue
                record = {"id": identity, "run": original_run, "card": card,
                          "brief": entry.get("brief", accompanying["brief.json"]),
                          "policy": entry.get("policy", accompanying["rubric.json"]),
                          "sources": accompanying["sources.json"], "original_record": entry,
                          "assessment": entry.get("assessment"), "review": entry.get("review"),
                          "tests": entry.get("tests", []), "identity_origin": identity_origin,
                          "artifacts": [str(path.resolve())]}
                if identity in records:
                    prior = records[identity]
                    if prior["card"] != card:
                        gaps.append({"path": str(path), "id": identity, "reason": "conflicting retained card; earlier export retained, conflicting bytes archived"})
                    prior["artifacts"].append(str(path.resolve()))
                else:
                    records[identity] = record
        except Exception as error:
            gaps.append({"path": str(path), "reason": "unreadable/unsupported artifact", "error_type": type(error).__name__})
    return {"artifacts": artifacts, "records": list(records.values()), "gaps": gaps, "exports": export_summaries}


def summary(bundle):
    return {"artifacts": len(bundle["artifacts"]), "recoverable_hypotheses": len(bundle["records"]),
            "original_identity_records": sum(not r["identity_origin"].startswith("artifact-scoped") for r in bundle["records"]),
            "artifact_scoped_records": sum(r["identity_origin"].startswith("artifact-scoped") for r in bundle["records"]),
            "retained_events": sum(len(r["original_record"].get("events", [])) for r in bundle["records"]),
            "retained_tests": sum(len(r["tests"]) for r in bundle["records"]),
            "export_coverage": bundle["exports"], "unresolved_gaps": bundle["gaps"],
            "limits": ["Export global stats are not proof those records were exported.",
                       "Historical event timestamps/IDs are preserved verbatim in snapshots; reconstructed ledger events have import timestamps.",
                       "Only explicitly retained planned tests are restored as plans; measured outcomes are not inferred.",
                       "This is partial recovery, not a claim that the lost VM ledger is complete."]}


@contextlib.contextmanager
def writer_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".writer.lock").open("a+b") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Research state has an active writer; retry after it completes") from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def apply(bundle, state_root):
    root = Path(state_root).expanduser().resolve()
    result = summary(bundle)
    result.update(mode="applied", inserted=0, existing=0, planned_tests_restored=0, import_errors=[])
    with writer_lock(root):
        archive = root / "research/legacy-memory/artifacts"
        archive.mkdir(parents=True, exist_ok=True)
        for artifact in bundle["artifacts"].values():
            target = archive / (artifact["sha256"] + ".json")
            if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() != artifact["sha256"]:
                raise ValueError("Existing archived artifact checksum mismatch")
            if not target.exists():
                target.write_bytes(artifact["raw"])
        ledger = HypothesisMemory(root / "research/hypotheses.sqlite")
        try:
            for record in bundle["records"]:
                try:
                    existed = ledger.db.execute("SELECT 1 FROM hypotheses WHERE id=?", (record["id"],)).fetchone() is not None
                    identity = ledger.register(record["run"], record["card"], record["brief"], record["policy"],
                                               record["sources"], allow_unresolved_parents=True)
                    if identity != record["id"]:
                        raise ValueError("Identity unexpectedly changed")
                    original = record["original_record"]
                    reviews = [event["data"] for event in original.get("events", []) if event.get("type") == "reviewed"]
                    if reviews:
                        for review in reviews:
                            ledger.review(identity, review["assessment"], review.get("review", {}), record["policy"])
                    elif record["assessment"]:
                        ledger.review(identity, record["assessment"], record["review"] or {"legacy_import": True}, record["policy"])
                    provenance = {"original_id": identity, "original_run": record["run"], "identity_origin": record["identity_origin"],
                                  "artifacts": [{"original_path": p, "sha256": bundle["artifacts"][p]["sha256"]} for p in sorted(set(record["artifacts"]))]}
                    with ledger._transaction():
                        snapshot = ledger._node("legacy_hypothesis_snapshot", original)
                        ledger._edge(identity, "recovered_from", snapshot)
                        ledger._event(identity, "legacy_imported", provenance, "migration")
                    for test in record["tests"]:
                        if test.get("status") != "planned" or test.get("results"):
                            result["unresolved_gaps"].append({"id": identity, "test_id": test.get("id"), "reason": "historical test retained as snapshot only; non-plan lifecycle requires explicit receipt importer"})
                            continue
                        request_id = test.get("plan", {}).get("request_id")
                        if not request_id or "test:" + digest([identity, request_id]) != test.get("id"):
                            result["unresolved_gaps"].append({"id": identity, "test_id": test.get("id"), "reason": "test identity cannot be reconstructed without changing original ID"})
                            continue
                        previous = ledger.db.execute("SELECT 1 FROM tests WHERE id=?", (test["id"],)).fetchone()
                        ledger.plan_test(identity, test["plan"], test["scope"], actor="migration")
                        result["planned_tests_restored"] += int(previous is None)
                    result["existing" if existed else "inserted"] += 1
                except Exception as error:
                    result["import_errors"].append({"id": record["id"], "error_type": type(error).__name__, "reason": "Immutable conflict or unsupported record; original artifact retained"})
            result["ledger_stats"] = ledger.stats()
        finally:
            ledger.db.close()
        manifest = {"summary": result, "artifacts": {p: {k: v for k, v in a.items() if k != "raw"} for p, a in bundle["artifacts"].items()}}
        content = json.dumps(manifest, sort_keys=True, indent=2).encode()
        target = archive.parent / ("import-" + hashlib.sha256(content).hexdigest() + ".json")
        target.write_bytes(content)
        result["manifest"] = str(target)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", required=True, help="Retained runs root; repeat for multiple sources")
    parser.add_argument("--original-root", action="append", default=[], help="Additional original runs root to resolve hashed historical IDs")
    parser.add_argument("--state-root", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    bundle = collect(args.source, args.original_root)
    result = apply(bundle, args.state_root) if args.apply else {"mode": "dry_run", **summary(bundle)}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
