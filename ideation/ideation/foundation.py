"""Portable research CLI. All network/cloud/model work is explicitly selected."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import gzip
import json
import os
import sqlite3
import sys
import tempfile
import uuid
from pathlib import Path

DEFAULT_STATE = Path.home() / ".local/share/inference-autoresearch"


class PublicationError(RuntimeError):
    """Local state is durable on disk, but configured remote publication failed."""
    def __init__(self, receipt, cause):
        super().__init__("Local snapshot retained; configured publication failed")
        self.receipt = receipt
        self.cause_type = type(cause).__name__



class ExperimentMutationError(RuntimeError):
    """An experiment operation failed after its journal was snapshotted."""
    def __init__(self, receipt, cause):
        super().__init__("Experiment operation failed; committed journal was snapshotted")
        self.receipt = receipt
        self.cause_type = type(cause).__name__


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _read(path, default=None):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else default


@contextlib.contextmanager
def _locked(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".writer.lock").open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def _namespace_root(root, namespace):
    if namespace == "research":
        return root / "research"
    if namespace == "experiments/registry":
        return root / "experiments"
    raise ValueError("CLI namespace must be research or experiments/registry")


class StateNotInitializedError(ValueError):
    """Safe actionable error; contains no provider URL or credential values."""


class SourceLookupError(KeyError):
    """Local absence, distinct from provider failure; messages contain no inputs."""

    def __init__(self, *, revision=False):
        self.error_code = "source_revision_not_retained" if revision else "source_not_retained"
        self.safe_message = (
            "This source revision is not retained locally. Inspect show ID --history for available revisions; do not substitute the current revision silently. No provider request was made."
            if revision else
            "This source is not retained in the selected local corpus. Check the source ID and corpus coverage; use explicit online discovery or repository refresh if needed. Local absence does not prove upstream absence. No provider request was made."
        )
        super().__init__(self.safe_message)


def _config(root, args):
    from .discovery import load_config, validate
    path = Path(args.config).expanduser() if getattr(args, "config", None) else root / "research/config.json"
    if not path.exists():
        raise StateNotInitializedError("Run researchctl init or supply --config")
    config = load_config(path)
    if getattr(args, "repo", None):
        config["repositories"] = args.repo
    if getattr(args, "query", None):
        config["queries"] = config.get("queries", []) + [{"provider": "arxiv", "query": query} for query in args.query]
    if getattr(args, "recent_days", None) is not None:
        config["recency_days"] = args.recent_days
        config["github_initial_days"] = args.recent_days
    if getattr(args, 'only', 'all') == 'github':
        config['budgets'] = {**config['budgets'], 'paper_requests': 0, 'citation_requests': 0}
    elif getattr(args, 'only', 'all') == 'papers':
        config['repositories'] = []
        config['budgets'] = {**config['budgets'], 'github_pages': 0}
    return validate(config)


def _lineage(root):
    return _read(root / "lineage.json", {})


def _set_lineage(root, namespace, identity, action):
    value = _lineage(root)
    value[namespace] = {"id": identity, "action": action, "at": dt.datetime.now(dt.timezone.utc).isoformat()}
    _write(root / "lineage.json", value)


def _snapshot(root, namespace, *, publish=True):
    from .storage import snapshot
    # Keep operational journaling out of an uninitialized restore destination.
    # Research snapshots retain a consistent copy, without changing who owns
    # the active local command journal after restore.
    if namespace == "research" and (root / "commands.sqlite").exists():
        from .journal import connect
        connect(root).close()  # Merge restored provenance before retaining it.
        from .storage import _sqlite_backup
        _sqlite_backup(root / "commands.sqlite", root / "research/command-history.sqlite")
    parent = _lineage(root).get(namespace, {}).get("id")
    result = snapshot(_namespace_root(root, namespace), root / "archives", namespace=namespace, parent=parent)
    latest = _read(root / "latest-snapshots.json", {})
    latest[namespace] = result["id"]
    _write(root / "latest-snapshots.json", latest)
    receipt = {"id": result["id"], "namespace": namespace, "parent": parent,
               "files": len(result["files"]), "total_bytes": result["total_bytes"], "skipped": result["skipped"],
               "published": False}
    remote = _read(root / "remote.json", {})
    if not publish and remote.get("auto_publish"):
        receipt["publication_skipped"] = "offline operation"
    if publish and remote.get("auto_publish"):
        from .storage import push
        try:
            # Parent came from this writer's successful publication/restore.
            # Never adopt a newly observed remote head to bypass a conflict.
            uploaded = push(root / "archives", _transport(argparse.Namespace(**remote)),
                            result["id"], namespace=namespace, expected_head=parent)
            _set_lineage(root, namespace, result["id"], "published")
            receipt.update(published=True, publication=uploaded)
        except Exception as error:
            receipt.update(publication_failed=True, publication_error_type=type(error).__name__)
            _write(root / "publication-failure.json", receipt)
            raise PublicationError(receipt, error) from error
    if namespace == "research" and (root / "pending-research-checkpoint.json").exists():
        _write(root / "pending-research-checkpoint.json", {
            "snapshot_required": False, "published": receipt["published"],
            "snapshot_id": receipt["id"], "at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "meaning": "Checkpoint captured pending research; published reports this checkpoint only"})
    return receipt


def _research_snapshot(root, args, *, publish):
    """Opt-in interactive durability: local commits survive; backup is explicit."""
    if not getattr(args, "defer_snapshot", False):
        return _snapshot(root, "research", publish=publish)
    receipt = {"namespace": "research", "deferred": True, "published": False,
               "local_state_retained": True, "snapshot_required": True,
               "at": dt.datetime.now(dt.timezone.utc).isoformat(),
               "command": args.command,
               "next_action": "researchctl snapshot --namespace research",
               "meaning": "Local source records, receipts and journal retained; no new recovery snapshot or S3 backup yet"}
    _write(root / "pending-research-checkpoint.json", receipt)
    return receipt


def _transport(args):
    from .storage import LocalTransport, S3Transport
    if args.local_remote:
        return LocalTransport(Path(args.local_remote).expanduser())
    if args.bucket:
        return S3Transport(args.bucket, prefix=args.prefix, profile=args.profile, region=args.region)
    raise ValueError("Choose --local-remote or --bucket")


def _manifest_id(root, args):
    identity = args.manifest_id or _read(root / "latest-snapshots.json", {}).get(args.namespace)
    if not identity:
        raise ValueError("Supply --manifest-id or create a local snapshot first")
    return identity


def _document_order(document):
    def timestamp(value):
        if not value:
            return float("-inf")
        try:
            value = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
            if value.tzinfo is None:
                value = value.replace(tzinfo=dt.timezone.utc)
            return value.timestamp()
        except (ValueError, TypeError, AttributeError):
            return float("-inf")
    return (timestamp(document.get("updated_at") or document.get("created_at") or document.get("fetched_at")),
            timestamp(document.get("fetched_at")))


def _import_jsonlines(source, destination):
    """Import retained normalized documents; source remains untouched."""
    source = Path(source).expanduser().resolve(strict=True)
    counts = {"documents_seen": 0, "documents_imported": 0, "newer_local_preserved": 0}
    opener = gzip.open if source.suffix == ".gz" else open
    try:
        destination.db.execute("BEGIN IMMEDIATE")
        with opener(source, "rt", encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                incoming = json.loads(line)
                for field in ("metadata", "tags"):
                    if isinstance(incoming.get(field), str):
                        incoming[field] = json.loads(incoming[field])
                current = destination.get(incoming["id"])
                incoming_date = _document_order(incoming)
                current_date = _document_order(current) if current else (float("-inf"), float("-inf"))
                # put retains the incoming revision even if the newer local
                # projection must immediately be restored in this transaction.
                destination.put(incoming)
                counts["documents_seen"] += 1
                if current and current_date > incoming_date:
                    destination.put(current)
                    counts["newer_local_preserved"] += 1
                else:
                    counts["documents_imported"] += 1
        destination.db.commit()
    except BaseException:
        destination.db.rollback()
        raise
    return {**counts, "source": str(source), "source_open_mode": "readonly-jsonlines", "source_modified": False}


def _import_corpus(source, destination):
    """Merge a read-only old corpus; preserve newer target records and conflicts."""
    from .store import Store
    source = Path(source).expanduser().resolve(strict=True)
    if source.name.endswith((".jsonl", ".jsonl.gz", ".ndjson", ".ndjson.gz")):
        return _import_jsonlines(source, destination)
    if source == destination.path.resolve():
        raise ValueError("Source and destination corpus must differ")
    source_identity = hashlib.sha256(str(source).encode()).hexdigest()[:20]
    counts = {"documents_seen": 0, "documents_imported": 0, "newer_local_preserved": 0,
              "revisions_imported": 0, "edges_imported": 0, "historical_derived_edges_skipped": 0, "checkpoints_imported": 0,
              "checkpoint_conflicts_preserved": 0}
    preserved_newer = set()
    with contextlib.closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as original:
        original.row_factory = sqlite3.Row
        original.execute("BEGIN")
        tables = {row[0] for row in original.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "documents" not in tables:
            raise ValueError("Source is not a supported corpus database")
        try:
            destination.db.execute("BEGIN IMMEDIATE")
            for row in original.execute("SELECT * FROM documents"):
                raw = dict(row)
                incoming = Store.decode(raw)
                current = destination.get(incoming["id"])
                counts["documents_seen"] += 1
                incoming_date = _document_order(incoming)
                current_date = _document_order(current) if current else (float("-inf"), float("-inf"))
                # Preserve original content-hash receipts even if Store's hash algorithm changed.
                if raw.get("content_hash"):
                    changed = destination.db.execute("INSERT OR IGNORE INTO document_revisions VALUES(?,?,?,?)",
                        (raw["id"], raw["content_hash"], raw.get("fetched_at", ""), json.dumps(raw, sort_keys=True))).rowcount
                    counts["revisions_imported"] += changed
                if current and current_date > incoming_date:
                    preserved_newer.add(incoming["id"])
                    counts["newer_local_preserved"] += 1
                else:
                    destination.put(incoming)
                    counts["documents_imported"] += 1
            if "document_revisions" in tables:
                for row in original.execute("SELECT id,content_hash,observed_at,document FROM document_revisions"):
                    # Validate JSON; preserve exact historical payload and identity.
                    json.loads(row["document"])
                    counts["revisions_imported"] += destination.db.execute(
                        "INSERT OR IGNORE INTO document_revisions VALUES(?,?,?,?)", tuple(row)).rowcount
            if "edges" in tables:
                for row in original.execute("SELECT src,relation,dst,evidence,detail FROM edges"):
                    if row["evidence"] in preserved_newer and row["relation"] in {"mentions", "links_to", "child_of"}:
                        counts["historical_derived_edges_skipped"] += 1
                        continue
                    json.loads(row["detail"])
                    counts["edges_imported"] += destination.db.execute("INSERT OR IGNORE INTO edges VALUES(?,?,?,?,?)", tuple(row)).rowcount
            if "checkpoints" in tables:
                for row in original.execute("SELECT key,value FROM checkpoints"):
                    json.loads(row["value"])
                    current = destination.db.execute("SELECT value FROM checkpoints WHERE key=?", (row["key"],)).fetchone()
                    if not current:
                        destination.db.execute("INSERT INTO checkpoints VALUES(?,?)", tuple(row))
                        counts["checkpoints_imported"] += 1
                    elif json.loads(current[0]) != json.loads(row["value"]):
                        key = "imported:" + source_identity + ":" + hashlib.sha256(row["value"].encode()).hexdigest()[:12] + ":" + row["key"]
                        destination.db.execute("INSERT OR IGNORE INTO checkpoints VALUES(?,?)", (key, row["value"]))
                        counts["checkpoint_conflicts_preserved"] += 1
            destination.db.commit()
        except BaseException:
            destination.db.rollback()
            raise
    return {**counts, "source": str(source), "source_open_mode": "readonly", "source_modified": False}


def _run_research(root, args):
    from .store import Store
    from . import discovery
    config = _config(root, args)
    if not 0 <= args.deep_count <= 20:
        raise ValueError("deep-count must be 0..20")
    if args.reason and args.offline:
        raise ValueError("--offline cannot enable model reasoning; use a separate online --reason run")
    if args.reason and not args.brief:
        raise ValueError("--reason requires --brief with explicit baseline and objective")
    store = Store(root / "research/corpus.sqlite")
    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
    out = root / "research/records" / run_id
    out.mkdir(parents=True)
    result = {"run_id": run_id, "output": str(out), "question": args.question,
              "offline": args.offline, "GPU_experiments": 0}
    try:
        _write(out / "config.json", config)
        if not args.offline and args.command != "investigate":
            result["refresh"] = discovery.refresh(store, config)
            _write(out / "refresh.json", result["refresh"])
        candidates = discovery.shortlist(store, config)
        _write(out / "shortlist.json", candidates)
        query_hits = store.search(args.question, limit=max(1, args.deep_count))
        chosen = list(dict.fromkeys(args.source_id or ([doc["id"] for doc in query_hits] + [item["id"] for item in candidates])))[:args.deep_count]
        result["selected_sources"] = chosen
        if chosen:
            from .deep_dive import investigate
            brief = str(Path(args.brief).expanduser().resolve()) if args.brief else None
            result["dossier"] = investigate(store, args.question, chosen, out / "dossier",
                max_http_calls=0 if args.offline else args.max_http_calls,
                max_fulltexts=args.deep_count, max_repositories=args.max_repositories,
                repositories=args.repository, code_sources=args.code_source,
                reason=args.reason, brief=brief, model=args.model, timeout=args.timeout)
            if args.reason:
                from .research_flow import retain_reasoned_packet
                result["typed_evidence"] = retain_reasoned_packet(root, result["dossier"]["evidence"]["packet"], out / "dossier/hypotheses")
        else:
            result["status"] = "no_selected_sources"
        _write(out / "run.json", result)
    except BaseException as error:
        result.update(status="failed", error_type=type(error).__name__)
        _write(out / "run.json", result)
        raise
    finally:
        store.db.commit()
        store.db.close()
        result["snapshot"] = _research_snapshot(root, args, publish=not args.offline and not args.local_only)
        _write(out / "snapshot-receipt.json", result["snapshot"])
    return result


def _execute(root, args):
    command = args.command
    replica = None
    if args.replica:
        if command not in {"search", "pr-search", "show", "status"} or command == "show" and args.claims:
            raise ValueError("Replica access supports only search, show and status")
        replica = _read(root / "replicas/research/CURRENT.json")
        if not replica:
            raise ValueError("No downloaded research replica; run sync-replica first")
    if command == "paper-search":
        from .paper_search import search_papers
        from .store import Store
        if not (root / 'research/config.json').exists():
            raise StateNotInitializedError('Run researchctl init first')
        store = Store(root / 'research/corpus.sqlite')
        output = root / 'research/records' / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S') + '-paper-search-' + uuid.uuid4().hex[:8])
        try:
            result = search_papers(store, args.query_text, args.provider, args.after, args.before, args.limit)
            result['output'] = str(output)
            _write(output / 'search.json', result)
        finally:
            store.db.close()
        result['snapshot'] = _research_snapshot(root, args, publish=not args.local_only)
        return result
    if command in {"doctor", "costs"}:
        if command == "costs":
            return {"supported": False, "reason": "Reconciled provider billing is not implemented; logical calls are not costs. Unknown spend is not zero.", "default_model_calls": 0, "default_gpu_calls": 0}
        import importlib.util
        result = {"state_dir": str(root), "provider_credentials_present": {key: bool(os.environ.get(key)) for key in ("GITHUB_TOKEN", "OPENALEX_API_KEY", "SERPER_API_KEY")},
                  "mcp_installed": importlib.util.find_spec("mcp") is not None, "network_checked": False, "serving_checked": False}
        path = root / "research/corpus.sqlite"
        if path.exists():
            db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
            try:
                result["corpus"] = {"quick_check": db.execute("PRAGMA quick_check").fetchone()[0], "documents": db.execute("SELECT count(*) FROM documents").fetchone()[0]}
            finally:
                db.close()
        else:
            result["corpus"] = {"initialized": False}
        return result
    flow_hypothesis = command == "hypothesis" and args.hypothesis_command in {"propose", "show"}
    if command in {"claim", "screen", "eval-plan", "decide", "changes", "link-evidence"} or flow_hypothesis:
        from .research_flow import ResearchFlow
        flow = ResearchFlow(root)
        mutation = command not in {"changes"} and not (command == "claim" and args.claim_command == "show") and not (flow_hypothesis and args.hypothesis_command == "show")
        try:
            record = _read(Path(args.record).expanduser()) if getattr(args, "record", None) else None
            if command == "claim":
                result = flow.claim(record) if args.claim_command == "record" else {"id": args.id, **flow.node(args.id, "claim")}
            elif command == "link-evidence":
                result = flow.link(args.id, args.claim_id, args.relation, args.rationale)
            elif flow_hypothesis:
                result = flow.propose(record) if args.hypothesis_command == "propose" else flow.dossier(args.id)
            elif command == "screen":
                result = flow.screen(args.id, record)
            elif command == "eval-plan":
                result = flow.eval_plan(args.id, record)
            elif command == "decide":
                result = flow.decide(args.id, record)
            else:
                result = flow.changes(args.cursor, args.limit)
        finally:
            flow.close()
            if mutation:
                snapshot = _research_snapshot(root, args, publish=not args.local_only)
        return {"record": result, "snapshot": snapshot} if mutation else result
    if command == "backfill":
        from . import backfill
        if args.backfill_command == "start":
            return backfill.start(root, env_file=args.env_file, publish_every=args.publish_every)
        if args.backfill_command == "stop":
            return backfill.stop(root)
        return backfill.status(root)
    if command == "history":
        from .journal import history
        return history(root, args.limit)
    if command in {"expand", "prescreen"}:
        from .controls import expand_query, prescreen
        if command == "expand":
            plan = None
            if args.plan:
                plan = json.loads(Path(args.plan).expanduser().read_text())
                if not isinstance(plan, dict):
                    raise ValueError('Explicit query plan must be a JSON object')
            value = expand_query(args.question, _config(root, args), after=args.after, before=args.before,
                                 plan=plan)
        else:
            value = prescreen(_read(Path(args.record).expanduser()))
        output = root / "research/records" / (command + "-" + uuid.uuid4().hex)
        _write(output / "result.json", value)
        return {"output": str(output), "result": value, "snapshot": _research_snapshot(root, args, publish=False)}
    if command == "hypothesis":
        from .chat_memory import persist_card, recall_cards
        if args.hypothesis_command == "recall":
            return recall_cards(root, query=args.query, limit=args.limit)
        try:
            result = persist_card(root, _read(Path(args.record).expanduser()))
        finally:
            snapshot = _research_snapshot(root, args, publish=not args.local_only)
        return {"record": result, "snapshot": snapshot}
    if command == "sync-replica":
        from .replica import sync
        return sync(root, _transport(args), args.namespace, args.manifest_id)
    if command == "remote":
        if args.remote_command == "show":
            return {"configured": (root / "remote.json").exists(), "remote": _read(root / "remote.json", None), "external_actions": 0}
        if args.remote_command == "disable":
            remote = _read(root / "remote.json", {})
            remote["auto_publish"] = False
            _write(root / "remote.json", remote)
            return {"remote": remote, "external_actions": 0}
        remote = {"bucket": args.bucket, "local_remote": args.local_remote, "prefix": args.prefix,
                  "profile": args.profile, "region": args.region, "auto_publish": args.auto_publish}
        if args.bucket:
            from .storage import bucket_plan
            bucket_plan(args.bucket, args.region, args.prefix)  # Validate locally; no AWS client.
        else:
            path = Path(args.local_remote).expanduser().resolve()
            if path == root or path in root.parents or root in path.parents:
                raise ValueError("Remote directory must be separate from local state")
            remote["local_remote"] = str(path)
        _write(root / "remote.json", remote)
        return {"remote": remote, "external_actions": 0,
                "meaning": "Future local snapshots publish automatically only when auto_publish is enabled; configure does not upload."}
    if command == "bucket-plan":
        from .storage import bucket_plan, estimate_cost
        return {"plan": bucket_plan(args.bucket or "inference-autoresearch-example", args.region, args.prefix),
                "cost_estimate": estimate_cost(), "cloud_actions": 0}
    if command == "init":
        from .discovery import load_config
        from .store import Store
        default = Path(__file__).resolve().parents[1] / "config/discovery.json"
        config = load_config(args.config or default)
        target = root / "research/config.json"
        if target.exists():
            if _read(target) != config:
                raise ValueError("Existing config differs; edit it explicitly instead of resetting state")
        else:
            _write(target, config)
        store = Store(root / "research/corpus.sqlite")
        store.db.close()
        return {"state_dir": str(root), "config": str(target), "initialized": True,
                "network_calls": 0, "snapshot": _snapshot(root, "research", publish=False)}
    if command == "plan":
        from .discovery import plan
        return plan(_config(root, args))
    if command == "status":
        from .store import Store
        corpus = Path(replica["path"]) / "corpus.sqlite" if replica else root / "research/corpus.sqlite"
        result = {"state_dir": str(root), "lineage": _lineage(root), "latest_snapshots": _read(root / "latest-snapshots.json", {}),
                  "research_checkpoint": _read(root / "pending-research-checkpoint.json", None)}
        result["replica"] = replica or _read(root / "replicas/research/CURRENT.json")
        if corpus.exists():
            store = Store(corpus, readonly=bool(replica))
            try:
                result["research"] = store.stats()
            finally:
                store.db.close()
        else:
            result["research"] = {"initialized": False}
        path = root / "experiments/experiments.sqlite3"
        if path.exists():
            from .experiments import ExperimentRegistry
            registry = ExperimentRegistry(root)
            try:
                result["experiments"] = [{k: record[k] for k in ("id", "hypothesis_id", "baseline_id", "scope", "status")} for record in registry.list()]
            finally:
                registry.close()
        return result
    if command in {"refresh", "search", "pr-search", "show", "import-corpus"}:
        from .store import Store
        source_root = Path(replica["path"]) if replica else root / "research"
        if not (source_root / "config.json").exists():
            raise StateNotInitializedError("Run researchctl init first")
        store = Store(source_root / "corpus.sqlite", readonly=bool(replica))
        try:
            if command == "refresh":
                from .discovery import refresh, shortlist
                config = _config(root, args)
                run_id = "refresh-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:8]
                output = root / "research/records" / run_id
                _write(output / "config.json", config)
                result = {"status": "started", "run_id": run_id}
                try:
                    result.update(refresh(store, config, force=args.force))
                    result["shortlist"] = shortlist(store, config)
                except BaseException as error:
                    result.update(status="failed", error_type=type(error).__name__)
                    raise
                finally:
                    store.db.commit()
                    _write(output / "receipt.json", result)
                    receipt = _research_snapshot(root, args, publish=not args.local_only)
                result["snapshot"] = receipt
                result["output"] = str(output)
                return result
            if command in {"search", "pr-search"}:
                return store.search(args.query_text, match=args.match, after=args.after, before=args.before, limit=args.limit, offset=args.offset,
                                    date_field=args.date_field, kind="pr" if command == "pr-search" else args.kind,
                                    id_prefix="github:" + args.repo + ":" if args.repo else None)
            if command == "show":
                result = store.get(args.id)
                if result is None:
                    raise SourceLookupError()
                if args.revision_hash:
                    revisions = store.revisions(args.id)
                    result = next((r for r in revisions if r["content_hash"] == args.revision_hash), None)
                    if result is None:
                        raise SourceLookupError(revision=True)
                if args.history:
                    history = {"current": store.get(args.id), "revisions": store.revisions(args.id)}
                    if args.revision_hash:
                        history["selected_revision"] = result
                    return history
                if args.claims:
                    from .research_flow import ResearchFlow
                    flow = ResearchFlow(root)
                    try:
                        return {"source": result, "claims": flow.source_claims(args.id)}
                    finally:
                        flow.close()
                return result
            result = _import_corpus(args.source, store)
            result["snapshot"] = _snapshot(root, "research")
            return result
        finally:
            store.db.close()
    if command in {"run", "investigate"}:
        return _run_research(root, args)
    if command == "snapshot":
        return _snapshot(root, args.namespace, publish=not args.local_only)
    if command == "push":
        from .storage import push, ConflictError
        lineage = _lineage(root).get(args.namespace, {}).get("id")
        if args.expected_head != lineage:
            raise ConflictError("Expected head must match local previously published/restored lineage")
        identity = _manifest_id(root, args)
        result = push(root / "archives", _transport(args), identity, namespace=args.namespace, expected_head=args.expected_head)
        _set_lineage(root, args.namespace, identity, "published")
        return result
    if command == "pull":
        from .storage import pull
        result = pull(_transport(args), root / "archives", namespace=args.namespace, manifest_id=args.manifest_id)
        # Downloading is not adopting the remote state. Never update writer lineage.
        return {"namespace": args.namespace, "downloaded": True, "restored": False,
                "files": len(result["files"]), "manifest": result}
    if command == "restore":
        from .storage import restore
        if not args.manifest_id:
            raise ValueError("Restore requires --manifest-id; choose explicitly")
        destination = _namespace_root(root, args.namespace)
        result = restore(root / "archives", destination, args.manifest_id, namespace=args.namespace)
        _set_lineage(root, args.namespace, args.manifest_id, "restored")
        return {"id": args.manifest_id, "destination": str(destination), "files": len(result["files"])}
    if command == "experiment":
        from .experiments import ExperimentRegistry
        registry = ExperimentRegistry(root)
        try:
            sub = args.experiment_command
            if sub in {"create", "transition", "retain-artifacts"}:
                record = json.loads(Path(args.record).expanduser().read_text()) if sub != "retain-artifacts" else None
                mutation_error = None
                try:
                    if sub == "create":
                        result = registry.create(**record)
                    elif sub == "transition":
                        result = registry.transition(args.id, **record)
                    else:
                        result = registry.retain_artifacts(args.id)
                except Exception as error:
                    mutation_error = error
                finally:
                    # Event commit precedes bounded artifact retention. A later
                    # copy/index failure must not leave that journal local-only.
                    try:
                        receipt = _snapshot(root, "experiments/registry")
                    except PublicationError as error:
                        if mutation_error is not None:
                            error.mutation_error_type = type(mutation_error).__name__
                        raise
                if mutation_error is not None:
                    raise ExperimentMutationError(receipt, mutation_error) from mutation_error
                return {"retention" if sub == "retain-artifacts" else "experiment": result, "snapshot": receipt}
            if sub == "get":
                return registry.get(args.id)
            if sub == "list":
                return registry.list(status=args.status, scope=args.scope, hypothesis_id=args.hypothesis_id)
            if sub == "export":
                return registry.export(args.output)
        finally:
            registry.close()
    raise ValueError("Unsupported command")


def parser():
    p = argparse.ArgumentParser(prog="researchctl", description=__doc__)
    p.add_argument("--state-dir", default=os.environ.get("IDEATION_STATE_DIR") or os.environ.get("AUTORESEARCH_STATE_ROOT", str(DEFAULT_STATE)))
    p.add_argument("--env-file", help="Explicit local credential file; never copied into state")
    p.add_argument("--replica", action="store_true", help="Read downloaded VM replica for search/show/status; writer state untouched")
    p.add_argument("--local-only", action="store_true", help="New evidence/plan mutations snapshot locally; explicit later snapshot publishes")
    p.add_argument("--defer-snapshot", action="store_true", help="Interactive research only: retain local state/journal, checkpoint explicitly after the batch; no new snapshot/S3 backup per command")
    commands = p.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="Offline state initialization with resolved config")
    init.add_argument("--config")
    commands.add_parser("status")
    commands.add_parser("doctor", help="Local DB/credential-presence checks; does not spend API credits")
    commands.add_parser("costs", help="Report billing-ledger availability; unknown cost is not zero")
    papers = commands.add_parser('paper-search', help='Cached online keyword/date search; retain results and provenance')
    papers.add_argument('query_text')
    papers.add_argument('--provider', action='append', choices=('arxiv', 'openalex', 'hf'), help='Repeatable; default arxiv + openalex')
    papers.add_argument('--after')
    papers.add_argument('--before')
    papers.add_argument('--limit', type=int, default=10, help='1..20 per provider')
    claim = commands.add_parser("claim").add_subparsers(dest="claim_command", required=True)
    claim.add_parser("record").add_argument("--record", required=True)
    claim.add_parser("show").add_argument("id")
    for name in ("screen", "eval-plan", "decide"):
        step = commands.add_parser(name)
        step.add_argument("id", help="Persistent hypothesis ID")
        step.add_argument("--record", required=True)
        if name == "screen":
            step.add_argument("--mode", choices=("no-gpu",), default="no-gpu")
    link = commands.add_parser("link-evidence")
    link.add_argument("id")
    link.add_argument("--claim-id", required=True)
    link.add_argument("--relation", choices=("supports", "refutes", "background"), required=True)
    link.add_argument("--rationale", required=True)
    changes = commands.add_parser("changes")
    changes.add_argument("--cursor", type=int, default=0)
    changes.add_argument("--limit", type=int, default=100)
    history = commands.add_parser("history", help="Local command history; no credentials or raw arguments")
    history.add_argument("--limit", type=int, default=20)
    expand = commands.add_parser("expand", help="Offline bounded query expansion with taxonomy provenance")
    expand.add_argument("--question", required=True)
    expand.add_argument("--plan", help="Agent-authored semantic queries and observations JSON; validated offline")
    expand.add_argument("--config")
    expand.add_argument("--after")
    expand.add_argument("--before")
    prescreen = commands.add_parser("prescreen", help="Offline conditional ROI and cheapest diagnostic")
    prescreen.add_argument("--record", required=True)
    hypothesis = commands.add_parser("hypothesis").add_subparsers(dest="hypothesis_command", required=True)
    hypothesis.add_parser("record").add_argument("--record", required=True)
    hypothesis.add_parser("propose").add_argument("--record", required=True)
    hypothesis.add_parser("show").add_argument("id")
    recall = hypothesis.add_parser("recall")
    recall.add_argument("--query")
    recall.add_argument("--limit", type=int, default=20)
    backfill = commands.add_parser("backfill", help="Persistent resumable all-repository opening-record job").add_subparsers(dest="backfill_command", required=True)
    backfill.add_parser("start").add_argument("--publish-every", type=int, default=300)
    backfill.add_parser("status")
    backfill.add_parser("stop")
    def config_options(command):
        command.add_argument("--config")
        command.add_argument('--only', choices=('all', 'github', 'papers'), default='all', help='Select refresh sources for this invocation; saved config is unchanged')
        command.add_argument("--repo", action="append", help="Override repository list; repeatable")
        command.add_argument("--query", action="append", help="Additional arXiv search query; repeatable")
        command.add_argument("--recent-days", type=int)
    config_options(commands.add_parser("plan", help="Offline discovery plan"))
    refresh = commands.add_parser("refresh", help="Bounded API refresh and local durable snapshot")
    config_options(refresh)
    refresh.add_argument("--force", action="store_true")
    run = commands.add_parser("run", aliases=["investigate"], help="Refresh and investigate; investigate alias reads selected sources without refreshing other feeds")
    config_options(run)
    run.add_argument("--question", required=True)
    run.add_argument("--source-id", action="append")
    run.add_argument("--deep-count", type=int, default=3)
    run.add_argument("--offline", action="store_true", help="Skip refresh; only cached deep reads")
    run.add_argument("--reason", action="store_true", help="Explicit paid model reasoning; requires optional agents dependency")
    run.add_argument("--brief")
    run.add_argument("--model")
    run.add_argument("--timeout", type=int, default=300)
    run.add_argument("--max-http-calls", type=int, default=12)
    run.add_argument("--max-repositories", type=int, default=2)
    run.add_argument("--repository", action="append", help="Read only explicitly selected owner/repository READMEs; repeatable. Replaces automatic link selection, does not establish authorship")
    run.add_argument("--code-source", action="append", type=json.loads, help='Pinned file JSON: {"repo":"owner/name","ref":"40-hex commit","path":"relative/file.py"}; repeatable, at most 6 unique files')
    search = commands.add_parser("search", aliases=["pr-search"])
    search.add_argument("query_text")
    search.add_argument("--match", choices=("any", "all"), default="any", help="Match any or all lexical terms/quoted phrases")
    search.add_argument("--after")
    search.add_argument("--before")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--offset", type=int, default=0)
    search.add_argument("--date-field", choices=("created_at", "updated_at", "merged_at", "fetched_at"), default="updated_at")
    search.add_argument("--kind")
    search.add_argument("--repo")
    show = commands.add_parser("show")
    show.add_argument("id")
    show.add_argument("--history", action="store_true")
    show.add_argument("--revision-hash", help="Inspect an exact retained content revision")
    show.add_argument("--claims", action="store_true")
    imp = commands.add_parser("import-corpus")
    imp.add_argument("--source", required=True)
    for name in ("snapshot", "push", "pull", "restore", "sync-replica"):
        command = commands.add_parser(name)
        command.add_argument("--namespace", choices=("research", "experiments/registry"), default="research")
        if name != "snapshot":
            command.add_argument("--manifest-id")
        if name in {"push", "pull", "sync-replica"}:
            remote = command.add_mutually_exclusive_group(required=True)
            remote.add_argument("--local-remote")
            remote.add_argument("--bucket")
            command.add_argument("--prefix", default="autoresearch")
            command.add_argument("--profile")
            command.add_argument("--region", default="us-east-1")
        if name == "push":
            command.add_argument("--expected-head")
    remote = commands.add_parser("remote", help="Configure future snapshot publication; configuration itself is offline").add_subparsers(dest="remote_command", required=True)
    configure = remote.add_parser("configure")
    location = configure.add_mutually_exclusive_group(required=True)
    location.add_argument("--local-remote")
    location.add_argument("--bucket")
    configure.add_argument("--profile")
    configure.add_argument("--region", default="us-east-1")
    configure.add_argument("--prefix", default="autoresearch")
    configure.add_argument("--auto-publish", action="store_true")
    remote.add_parser("show")
    remote.add_parser("disable")
    bucket = commands.add_parser("bucket-plan", help="Local configuration and cost estimate; no cloud calls")
    bucket.add_argument("--bucket")
    bucket.add_argument("--region", default="us-east-1")
    bucket.add_argument("--prefix", default="autoresearch")
    experiment = commands.add_parser("experiment").add_subparsers(dest="experiment_command", required=True)
    create = experiment.add_parser("create")
    create.add_argument("--record", required=True)
    transition = experiment.add_parser("transition")
    transition.add_argument("id")
    transition.add_argument("--record", required=True)
    retention = experiment.add_parser("retain-artifacts", help="Retain small local evidence by hash without rewriting historical events")
    retention.add_argument("--id", help="Optional experiment ID; default all existing receipts")
    get = experiment.add_parser("get")
    get.add_argument("id")
    listing = experiment.add_parser("list")
    listing.add_argument("--status")
    listing.add_argument("--scope")
    listing.add_argument("--hypothesis-id")
    export = experiment.add_parser("export")
    export.add_argument("--output")
    return p


def invoke(argv=None):
    """Shared locked API for CLI and MCP; no stdout or exception text logging."""
    args = parser().parse_args(argv)
    if args.defer_snapshot and args.command not in {"paper-search", "expand", "prescreen", "investigate", "claim", "hypothesis", "screen", "eval-plan", "decide", "link-evidence", "snapshot", "search", "pr-search", "show", "history", "changes", "doctor", "status"}:
        raise ValueError("--defer-snapshot is restricted to interactive research; ingestion and experiment checkpoints remain immediate")
    root = Path(args.state_dir).expanduser().resolve()
    if args.env_file:
        os.environ["IDEATION_ENV_FILE"] = str(Path(args.env_file).expanduser().resolve())
    if args.env_file or args.command in {"refresh", "run", "investigate", "doctor", "paper-search"}:
        from .providers import load_provider_env
        load_provider_env()
    with _locked(root):
        from . import journal
        entry = journal.start(root, args)
        try:
            value = _execute(root, args)
        except BaseException as error:
            journal.finish(root, entry, error)
            raise
        else:
            journal.finish(root, entry)
    return value


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        value = invoke(argv)
        print(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))
        return 0
    except Exception as error:
        # Provider exception URLs can carry API keys. Never print their text.
        failure = {"error_type": type(error).__name__, "command": args.command,
                   "message": "Operation failed. State and existing snapshots were retained; check configuration, input records, credentials, or local lineage."}
        if isinstance(error, StateNotInitializedError):
            failure.update(error_code="state_not_initialized", message="Initialize this state directory with researchctl --state-dir PATH init, then retry. No provider request was made by this operation.")
        if isinstance(error, SourceLookupError):
            failure.update(error_code=error.error_code, message=error.safe_message)
        if isinstance(error, PublicationError):
            failure.update(message="Local snapshot retained, but configured remote publication failed. Resolve credentials/connectivity or reconcile lineage before retrying; remote HEAD was not adopted.",
                           snapshot=error.receipt, publication_error_type=error.cause_type)
        if isinstance(error, ExperimentMutationError):
            failure.update(message="Experiment operation failed, possibly during evidence retention; committed journal state was snapshotted. Inspect the attempt before retrying; no event was rolled back or rewritten.",
                           snapshot=error.receipt, mutation_error_type=error.cause_type)
        if getattr(error, "mutation_error_type", None):
            failure["mutation_error_type"] = error.mutation_error_type
        print(json.dumps(failure), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
