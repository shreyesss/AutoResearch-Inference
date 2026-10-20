"""Append-only hypothesis ledger and small SQLite graph; no graph service required.

Selection decisions and scoped experimental outcomes are deliberately independent.
A recorded verdict attests to an operator/evaluator report and artifact integrity,
not independent verification of that report.
"""
import hashlib
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from .store import now


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def fingerprint(card):
    text = " ".join(str(card.get("mechanism", "")).lower().split()) + "|" + " ".join(str(card.get("proposed_change", "")).lower().split())
    return hashlib.sha256(text.encode()).hexdigest()


class HypothesisMemory:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path), timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY, kind TEXT NOT NULL, data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS hypotheses(
          id TEXT PRIMARY KEY REFERENCES nodes(id), run TEXT NOT NULL, local_id TEXT NOT NULL,
          fingerprint TEXT NOT NULL, baseline TEXT NOT NULL, created_at TEXT NOT NULL,
          UNIQUE(run, local_id));
        CREATE INDEX IF NOT EXISTS hypotheses_fingerprint ON hypotheses(fingerprint);
        CREATE TABLE IF NOT EXISTS events(
          seq INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT UNIQUE NOT NULL,
          hypothesis_id TEXT REFERENCES hypotheses(id), type TEXT NOT NULL,
          at TEXT NOT NULL, actor TEXT NOT NULL, data TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS events_hypothesis ON events(hypothesis_id,seq);
        CREATE TABLE IF NOT EXISTS edges(
          src TEXT NOT NULL, relation TEXT NOT NULL, dst TEXT NOT NULL,
          evidence TEXT NOT NULL DEFAULT '', PRIMARY KEY(src,relation,dst,evidence));
        CREATE INDEX IF NOT EXISTS edges_dst ON edges(dst);
        CREATE TABLE IF NOT EXISTS tests(
          id TEXT PRIMARY KEY REFERENCES nodes(id), hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id));
        """)
        # Audit rows cannot accidentally be edited/deleted, even through direct SQL.
        for table in ("nodes", "hypotheses", "events", "edges", "tests"):
            for operation in ("UPDATE", "DELETE"):
                self.db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{operation} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT, 'memory is append-only'); END")
        self.db.commit()

    @contextmanager
    def _transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    def _node(self, kind, value, identity=None):
        identity = identity or kind + ":" + digest(value)
        raw = encoded(value)
        existing = self.db.execute("SELECT kind,data FROM nodes WHERE id=?", (identity,)).fetchone()
        if existing and (existing["data"] != raw or existing["kind"] != kind):
            raise ValueError("Conflicting immutable snapshot: " + identity)
        self.db.execute("INSERT OR IGNORE INTO nodes VALUES(?,?,?)", (identity, kind, raw))
        return identity

    def _edge(self, src, relation, dst, evidence=""):
        self.db.execute("INSERT OR IGNORE INTO edges VALUES(?,?,?,?)", (src, relation, dst, evidence))

    def _require(self, identity):
        if not self.db.execute("SELECT 1 FROM hypotheses WHERE id=?", (identity,)).fetchone():
            raise ValueError("Unknown hypothesis: " + str(identity))

    def _event(self, identity, kind, data, actor="operator"):
        event_id = "event:" + digest([identity, kind, data, actor])
        self.db.execute("INSERT OR IGNORE INTO events(id,hypothesis_id,type,at,actor,data) VALUES(?,?,?,?,?,?)",
                        (event_id, identity, kind, now(), actor, encoded(data)))
        row = self.db.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        value = dict(row)
        value["data"] = json.loads(value["data"])
        self._node("event", value, event_id)
        if identity:
            self._edge(identity, kind, event_id)
        return value

    @staticmethod
    def identity(run, local_id):
        return "hypothesis:" + digest([str(run), str(local_id)])

    def register(self, run, card, brief, policy, sources=(), *, allow_unresolved_parents=False):
        if not isinstance(card, dict) or not card.get("id"):
            raise ValueError("A proposal requires its local id")
        identity = self.identity(run, card["id"])
        snapshot = {"card": card, "brief": brief, "policy": policy}
        baseline = brief.get("baseline", {})
        with self._transaction():
            self._node("hypothesis", snapshot, identity)
            baseline_id = self._node("baseline", baseline)
            self.db.execute("INSERT OR IGNORE INTO hypotheses VALUES(?,?,?,?,?,?)",
                            (identity, str(run), str(card["id"]), fingerprint(card), baseline_id, now()))
            self._edge(identity, "against_baseline", baseline_id)
            self._edge(identity, "addresses_task", self._node("task", brief))
            self._edge(identity, "uses_policy", self._node("policy", policy))
            self._edge(identity, "produced_in", self._node("run", {"path": str(run)}))
            for parent in card.get("parents", []):
                parent_id = parent if str(parent).startswith("hypothesis:") else self.identity(run, parent)
                if parent_id == identity:
                    raise ValueError("A hypothesis cannot be its own parent")
                if not allow_unresolved_parents:
                    self._require(parent_id)
                self._edge(identity, "derived_from", parent_id)
            source_values = sources.values() if isinstance(sources, dict) else sources
            source_map = {s["id"]: s for s in source_values}
            for citation in card.get("evidence", []):
                source = source_map.get(citation.get("source_id"), {"id": citation.get("source_id"), "snapshot_missing": True})
                source_id = self._node("source", source)
                citation_id = self._node("citation", citation)
                self._edge(identity, citation.get("relation", "context"), source_id, citation_id)
            for other in self.db.execute("SELECT id FROM hypotheses WHERE fingerprint=? AND id<>?", (fingerprint(card), identity)):
                self._edge(identity, "same_mechanism_as", other["id"])
            self._event(identity, "produced", {"run": str(run), "local_id": str(card["id"])}, "generator")
        return identity

    def review(self, identity, assessment, review, policy=None, context=None):
        status = assessment.get("status") or ("accepted" if assessment.get("eligible") else "rejected")
        if status not in ("accepted", "deferred", "rejected", "superseded", "proposed"):
            raise ValueError("Unknown selection status: " + status)
        with self._transaction():
            self._require(identity)
            data = {"status": status, "assessment": assessment, "review": review}
            if policy is not None:
                data["policy_id"] = self._node("policy", policy)
                self._edge(identity, "reviewed_under", data["policy_id"])
            if context is not None:
                data["context_id"] = self._node("review_context", context)
                self._edge(identity, "review_context", data["context_id"])
                for source in context.get("sources", []):
                    self._edge(data["context_id"], "consulted", self._node("source", source))
            return self._event(identity, "reviewed", data, "reviewer")

    def plan_test(self, identity, plan, scope, actor="operator"):
        if not isinstance(plan, dict) or not plan or not isinstance(scope, dict) or not scope:
            raise ValueError("Test plan and explicit baseline/workload scope are required")
        # Supply request_id for retry-safe agent calls; omit for a distinct repeat test.
        request_id = plan.get("request_id") or str(uuid.uuid4())
        test_id = "test:" + digest([identity, request_id])
        data = {"id": test_id, "hypothesis_id": identity, "plan": plan, "scope": scope}
        with self._transaction():
            self._require(identity)
            self._node("test", data, test_id)
            self.db.execute("INSERT OR IGNORE INTO tests VALUES(?,?)", (test_id, identity))
            self._edge(identity, "tested_by", test_id)
            self._edge(test_id, "in_scope", self._node("scope", scope))
            self._event(identity, "test_planned", data, actor)
        return data

    def _test(self, test_id):
        row = self.db.execute("SELECT n.data FROM tests t JOIN nodes n ON n.id=t.id WHERE t.id=?", (test_id,)).fetchone()
        if not row:
            raise ValueError("Unknown test: " + test_id)
        return json.loads(row["data"])

    def start_test(self, test_id, actor="operator"):
        with self._transaction():
            test = self._test(test_id)
            if self._results(test_id):
                raise ValueError("Completed tests cannot restart; create a repeat test")
            return self._event(test["hypothesis_id"], "test_running", {"test_id": test_id}, actor)

    def _results(self, test_id):
        return [json.loads(r["data"]) for r in self.db.execute("SELECT data FROM events WHERE type='test_result' AND hypothesis_id=? ORDER BY seq", (self._test(test_id)["hypothesis_id"],)) if json.loads(r["data"]).get("test_id") == test_id]

    def test_result(self, test_id, verdict, artifact, note, actor="operator"):
        if verdict not in ("validated", "invalidated", "inconclusive", "error"):
            raise ValueError("Verdict must be validated, invalidated, inconclusive, or error")
        artifact = Path(artifact).resolve()
        if not artifact.is_file():
            raise ValueError("A readable test artifact file is required")
        artifact_record = {"path": str(artifact), "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "bytes": artifact.stat().st_size}
        with self._transaction():
            test = self._test(test_id)
            data = {"test_id": test_id, "verdict": verdict, "scope": test["scope"], "artifact": artifact_record,
                    "note": str(note), "meaning": "Evaluator-reported outcome within this test scope; artifact hash verified, scientific conclusion not independently verified."}
            results = self._results(test_id)
            if results and any(r != data for r in results):
                raise ValueError("Test already has a result; create a repeat test to record new evidence")
            event = self._event(test["hypothesis_id"], "test_result", data, actor)
            self._edge(test_id, "result", event["id"])
            self._edge(test_id, "has_artifact", self._node("artifact", artifact_record))
            return event

    def get(self, identity):
        self._require(identity)
        row = dict(self.db.execute("SELECT * FROM hypotheses WHERE id=?", (identity,)).fetchone())
        row.update(json.loads(self.db.execute("SELECT data FROM nodes WHERE id=?", (identity,)).fetchone()["data"]))
        events = []
        for event in self.db.execute("SELECT * FROM events WHERE hypothesis_id=? ORDER BY seq", (identity,)):
            event = dict(event)
            event["data"] = json.loads(event["data"])
            events.append(event)
        row["events"] = events
        reviews = [e for e in events if e["type"] == "reviewed"]
        row["status"] = reviews[-1]["data"]["status"] if reviews else "proposed"
        row["assessment"] = reviews[-1]["data"]["assessment"] if reviews else None
        row["tests"] = []
        for test_row in self.db.execute("SELECT id FROM tests WHERE hypothesis_id=?", (identity,)):
            test = self._test(test_row["id"])
            results = self._results(test["id"])
            running = any(e["type"] == "test_running" and e["data"]["test_id"] == test["id"] for e in events)
            test.update(status=("error" if results[-1]["verdict"] == "error" else "completed") if results else ("running" if running else "planned"), results=results)
            row["tests"].append(test)
        # Never collapse outcomes across different baselines/workloads into a global truth label.
        scopes = {}
        for test in row["tests"]:
            for result in test["results"]:
                key = digest(result["scope"])
                summary = scopes.setdefault(key, {"scope": result["scope"], "verdicts": [], "test_ids": []})
                summary["verdicts"].append(result["verdict"])
                summary["test_ids"].append(test["id"])
        for summary in scopes.values():
            verdicts = set(summary["verdicts"])
            summary["status"] = "conflicting" if {"validated", "invalidated"} <= verdicts else (next(iter(verdicts)) if len(verdicts) == 1 else "mixed")
        row["outcomes_by_scope"] = list(scopes.values())
        test_states = {test["status"] for test in row["tests"]}
        row["experiment_status"] = ("running" if "running" in test_states else
            "tested" if "completed" in test_states else "failed" if "error" in test_states else
            "planned" if row["tests"] else "untested")
        return row

    def query(self, limit=30, status=None, baseline=None, text=None):
        limit = max(1, min(int(limit), 1000))
        results = []
        for r in self.db.execute("SELECT id FROM hypotheses ORDER BY created_at DESC,rowid DESC"):
            item = self.get(r["id"])
            if status and item["status"] != status and item["experiment_status"] != status and not any(s["status"] == status for s in item["outcomes_by_scope"]):
                continue
            if baseline and item["baseline"] != baseline and str(baseline).lower() not in encoded(item["brief"].get("baseline", {})).lower():
                continue
            if text and str(text).lower() not in encoded(item["card"]).lower():
                continue
            results.append({k: item[k] for k in ("id", "run", "local_id", "card", "fingerprint", "status", "baseline", "created_at", "assessment", "experiment_status", "outcomes_by_scope")})
            if len(results) >= limit:
                break
        return results

    def recall(self, brief, limit=12, max_chars=24000):
        """Budgeted lexical recall, not an embedding search or a relevance guarantee.

        Score = 8*exact-known-baseline + 2*task-token-overlap + target-token-overlap.
        Ties prefer records with outcomes/rejection and then newest creation time.
        All stored hypotheses are scanned; full records remain available through get().
        """
        limit = max(0, min(int(limit), 100))
        max_chars = max(2, int(max_chars))
        stop = {"the", "and", "for", "with", "from", "that", "this", "into", "what", "have", "only",
                "task", "target", "model", "gpu", "name", "true", "false", "none", "unknown", "instructions"}
        def tokens(value):
            return {word for word in re.findall(r"[a-z0-9][a-z0-9_.-]{2,}", encoded(value).lower()) if word not in stop}
        task_text = {k: brief[k] for k in ("name", "task", "instructions", "instruction", "question", "direction", "objective", "constraints") if k in brief}
        task_tokens, target_tokens = tokens(task_text), tokens(brief.get("target", {}))
        baseline = brief.get("baseline", {})
        known_baseline = bool(baseline) and not baseline.get("unknown", False) if isinstance(baseline, dict) else bool(baseline)
        baseline_id = "baseline:" + digest(baseline)
        candidates = []
        # No query() limit: even a relevant old rejection beyond 1000 rows is eligible.
        for row in self.db.execute("SELECT h.*,n.data FROM hypotheses h JOIN nodes n ON n.id=h.id"):
            value = json.loads(row["data"])
            card = value["card"]
            words = tokens({k: card.get(k, "") for k in ("statement", "title", "mechanism", "proposed_change", "observed_bottleneck", "applicability")})
            task_overlap, target_overlap = len(words & task_tokens), len(words & target_tokens)
            baseline_match = bool(known_baseline and row["baseline"] == baseline_id)
            score = 8 * baseline_match + 2 * task_overlap + target_overlap
            # Compact metadata reads avoid loading long source/test snapshots for every row.
            latest = self.db.execute("SELECT data FROM events WHERE hypothesis_id=? AND type='reviewed' ORDER BY seq DESC LIMIT 1", (row["id"],)).fetchone()
            assessment = json.loads(latest["data"]) if latest else {}
            outcome_count = self.db.execute("SELECT count(*) FROM events WHERE hypothesis_id=? AND type='test_result'", (row["id"],)).fetchone()[0]
            attention = int(bool(outcome_count)) + int(assessment.get("status") in ("rejected", "deferred"))
            candidates.append((score, attention, row["created_at"], row["id"], baseline_match, task_overlap, target_overlap))
        candidates.sort(reverse=True)
        result = []
        def short(value, size):
            value = str(value or "")
            return value if len(value) <= size else value[:size - 1] + "…"
        for score, _, _, identity, baseline_match, task_overlap, target_overlap in candidates:
            if len(result) >= limit:
                break
            item = self.get(identity)
            card = item["card"]
            outcomes = sorted(item["outcomes_by_scope"], key=lambda o: o["status"] in ("invalidated", "conflicting", "mixed"), reverse=True)
            selected_outcomes = []
            for outcome in outcomes[:3]:
                scope = outcome["scope"]
                if len(encoded(scope)) > 600:
                    scope = {"summary": short(encoded(scope), 600), "truncated": True}
                selected_outcomes.append({"scope": scope, "status": outcome["status"], "verdicts": sorted(set(outcome["verdicts"])), "test_ids": outcome["test_ids"][-2:]})
            summary = {"id": identity, "status": item["status"], "fingerprint": item["fingerprint"],
                "statement": short(card.get("statement", card.get("title")), 320),
                "mechanism": short(card.get("mechanism"), 500), "change": short(card.get("proposed_change", card.get("new_adaptation")), 400),
                "reasons": [short(r, 180) for r in (item["assessment"] or {}).get("reasons", [])[:3]],
                "baseline": item["baseline"], "experiment_status": item["experiment_status"], "outcomes": selected_outcomes,
                "omitted_outcome_scopes": max(0, len(outcomes) - len(selected_outcomes)),
                "recall": {"score": score, "known_baseline_match": baseline_match, "task_token_overlap": task_overlap,
                           "target_token_overlap": target_overlap, "method": "lexical_baseline_v1"},
                "detail": "Compact recall; use hypothesis.get with id for full evidence and event history."}
            if len(encoded(result + [summary])) <= max_chars:
                result.append(summary)
        return result

    def graph(self, identity):
        self._require(identity)
        edges = [dict(r) for r in self.db.execute("SELECT * FROM edges WHERE src=? OR dst=?", (identity, identity))]
        # Include test artifacts and critic retrieval context, with their provenance edges.
        children = {row["id"] for row in self.db.execute("SELECT id FROM tests WHERE hypothesis_id=?", (identity,))}
        children.update(e["dst"] for e in edges if e["relation"] == "review_context")
        for child in children:
            edges.extend(dict(r) for r in self.db.execute("SELECT * FROM edges WHERE src=?", (child,)))
        nodes = []
        for node_id in sorted({identity} | {e[k] for e in edges for k in ("src", "dst")} | {e["evidence"] for e in edges if e["evidence"]}):
            row = self.db.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
            nodes.append({"id": node_id, "kind": row["kind"], "data": json.loads(row["data"])} if row else {"id": node_id, "kind": "unresolved_parent"})
        return {"nodes": nodes, "edges": edges}

    def stats(self):
        return {"hypotheses": self.db.execute("SELECT count(*) FROM hypotheses").fetchone()[0],
                "events": self.db.execute("SELECT count(*) FROM events").fetchone()[0],
                "tests": self.db.execute("SELECT count(*) FROM tests").fetchone()[0],
                "nodes": self.db.execute("SELECT count(*) FROM nodes").fetchone()[0],
                "edges": self.db.execute("SELECT count(*) FROM edges").fetchone()[0]}

    def import_runs(self, root):
        """Import history and proposal artifacts, retaining all legacy revision stages."""
        counts = {"imported": 0, "existing": 0, "errors": [], "files": 0}
        root = Path(root)
        paths = set(root.glob("**/history.json")) | set(root.glob("**/propose-*.json"))
        paths = {p for p in paths if not p.name.endswith(".schema.json")}
        for name in ("draft.json", "final.json", "repair.json", "hypotheses.json"):
            paths.update(p for p in root.glob("**/" + name) if not (p.parent / "history.json").exists()
                         and (p.parent / "draft.json").exists())
        for history_path in sorted(paths):
            counts["files"] += 1
            try:
                value = json.loads(history_path.read_text())
                folder = history_path.parent
                def read(name, fallback):
                    path = folder / name
                    return json.loads(path.read_text()) if path.exists() else fallback
                brief = read("brief.json", {"legacy": True, "baseline": {"unknown": True}})
                policy = read("rubric.json", {"legacy": True, "policy_unknown": True})
                sources = read("sources.json", [])
                legacy = history_path.name in ("draft.json", "final.json", "repair.json", "hypotheses.json")
                run = str(folder.resolve() / history_path.stem) if legacy else str(folder.resolve())
                if isinstance(value, list):
                    history = value
                elif isinstance(value, dict) and isinstance(value.get("hypotheses"), list):
                    history = [{"card": c} for c in value["hypotheses"]]
                    if legacy:
                        for section in ("rejected_leads", "comparators"):
                            for index, lead in enumerate(value.get(section, [])):
                                statement = lead if isinstance(lead, str) else encoded(lead)
                                history.append({"card": {"id": section + ":" + str(index), "statement": statement,
                                    "mechanism": statement, "proposed_change": "", "legacy_partial_record": True,
                                    "legacy_section": section, "original_record": lead},
                                    "assessment": {"status": "rejected" if section == "rejected_leads" else "deferred",
                                                   "reasons": ["Original legacy " + section + "; no full hypothesis card or experiment recorded"]}})
                else:
                    raise ValueError("Unsupported proposal artifact shape; preserved on disk")
                for entry in history:
                    card = entry.get("card", entry)
                    identity = self.identity(run, card["id"])
                    existing = self.db.execute("SELECT data FROM nodes WHERE id=?", (identity,)).fetchone()
                    if existing:
                        old = json.loads(existing["data"])
                        def normalized(c):
                            return {**c, "parents": [p if str(p).startswith("hypothesis:") else self.identity(run, p) for p in c.get("parents", [])]}
                        if normalized(old["card"]) != normalized(card):
                            raise ValueError("Conflicting stored card in " + history_path.name + ": " + str(card["id"]))
                    else:
                        identity = self.register(run, card, brief, policy, sources, allow_unresolved_parents=True)
                    if "assessment" in entry:
                        self.review(identity, entry["assessment"], entry.get("review", {"legacy": True}), policy)
                    with self._transaction():
                        artifact = {"path": str(history_path.resolve()), "stage": history_path.stem,
                                    "card_sha256": digest(card), "legacy": legacy}
                        self._event(identity, "imported_from", artifact, "migration")
                        if legacy:
                            # Earlier and later versions remain distinct immutable proposals.
                            for previous in self.db.execute("SELECT id,run FROM hypotheses WHERE local_id=? AND id<>?", (str(card["id"]), identity)):
                                if Path(previous["run"]).parent == Path(run).parent:
                                    self._edge(identity, "legacy_revision_related_to", previous["id"])
                    counts["existing" if existing else "imported"] += 1
            except Exception as exc:
                counts["errors"].append({"path": str(history_path), "error": str(exc)})
        return counts

    def import_jsonl(self, path):
        """Preserve original legacy records, including outcomes without inventing test scopes."""
        counts = {"imported": 0, "existing": 0, "errors": []}
        path = Path(path)
        if not path.exists():
            return counts
        for number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                record = json.loads(line)
                run = record.get("run", "legacy")
                local_id = record.get("id", record.get("candidate_id", "unknown"))
                identity = self.identity(run, local_id)
                if not self.db.execute("SELECT 1 FROM hypotheses WHERE id=?", (identity,)).fetchone() and record.get("event") == "proposal":
                    self.register(run, {"id": local_id, "mechanism": record.get("mechanism", ""),
                        "proposed_change": record.get("change", ""), "legacy_partial_record": True,
                        "original_record": record}, {"legacy": True, "baseline": {"unknown": True}},
                        {"legacy": True, "policy_unknown": True})
                    if "assessment" in record:
                        self.review(identity, record["assessment"], record.get("critique", {}))
                with self._transaction():
                    if not self.db.execute("SELECT 1 FROM hypotheses WHERE id=?", (identity,)).fetchone():
                        identity = None
                    data = {"legacy_record": record, "origin": str(path.resolve()), "line": number}
                    event_id = "event:" + digest([identity, "legacy_record", data, "migration"])
                    exists = bool(self.db.execute("SELECT 1 FROM events WHERE id=?", (event_id,)).fetchone())
                    self._event(identity, "legacy_record", data, "migration")
                    counts["existing" if exists else "imported"] += 1
            except Exception as exc:
                counts["errors"].append({"line": number, "error": str(exc)})
        return counts
