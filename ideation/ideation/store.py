import datetime as dt
import hashlib
import json
import re
import sqlite3
from pathlib import Path

ALIASES = {
    "b200": ["b200", "blackwell"],
    "h100": ["h100", "hopper"],
    "deepseek-v4.1-flash": ["deepseek-v4.1-flash", "deepseek v4.1 flash", "deepseek_v4_1", "deepseek v4.1", "deepseek-v4.1"],
    "deepseek": ["deepseek", "deep seek"],
    "moe": ["moe", "mixture of experts", "meg amoe", "megamoe"],
    "mla": ["mla", "multi-head latent", "multihead latent"],
    "ttft": ["ttft", "time to first token", "prefill latency"],
    "tpot": ["tpot", "itl", "inter token latency", "inter-token latency", "time per output token", "decode latency"],
    "throughput": ["throughput", "tokens/s", "tokens per second", "tok/s"],
    "performance": ["perf", "performance", "latency", "speedup", "throughput", "ttft", "tpot", "itl"],
    "speculation": ["speculative", "speculation", "mtp", "eagle", "draft", "dspark"],
    "communication": ["allreduce", "all-reduce", "alltoall", "all-to-all", "deepep", "nvlink", "nvswitch"],
    "kv-cache": ["kv cache", "kv-cache", "prefix cache", "prefix caching"],
    "nvfp4": ["nvfp4", "fp4"],
}

def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def tags_for(text):
    lower = text.lower()
    return [tag for tag, aliases in ALIASES.items() if any(re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", lower) for a in aliases)]

def link_identity(url):
    m = re.search(r"github.com/([^/]+/[^/]+)/(?:issues|pull)/(\d+)", url)
    if m:
        return "github:" + m.group(1) + ":" + m.group(2)
    m = re.search(r"arxiv.org/(?:abs|pdf|html)/(\d{4}\.\d+)", url)
    if m:
        return "arxiv:" + m.group(1)
    m = re.search(r"huggingface.co/papers/(\d{4}\.\d+)", url)
    return "hf:" + m.group(1) if m else url

def fts_query(query, match="any"):
    # Literal token/phrase parsing prevents accidental FTS operator injection.
    terms = re.findall(r'"([^"]+)"|(\S+)', query)
    groups = []
    for phrase, token in terms:
        term = phrase or token
        aliases = ALIASES.get(term.lower(), [term])
        groups.append("(" + " OR ".join('"' + a.replace('"', '""') + '"' for a in aliases) + ")")
    return (" AND " if match == "all" else " OR ").join(groups)

# These describe our retrieval, not a change in the primary source. They remain
# in the latest document/first observed revision, but cannot create revisions by
# themselves (otherwise every cache hit or refetch duplicates corpus history).
_RETRIEVAL_METADATA = {"retrieval_cache", "pr_detail_fetched_at", "query", "retrieval_query", "effective_arxiv_query"}


def content_fingerprint(doc):
    metadata = doc.get("metadata", {})
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    if isinstance(metadata, dict):
        metadata = {k: v for k, v in metadata.items() if k not in _RETRIEVAL_METADATA}
    material = {k: doc.get(k) for k in ("source", "kind", "url", "title", "body", "created_at", "updated_at", "state", "merged_at", "parent")}
    material["metadata"] = metadata
    return hashlib.sha256(json.dumps(material, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


class Store:
    def __init__(self, path, *, readonly=False):
        self.path = Path(path)
        if readonly:
            self.db = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True, timeout=30)
            self.db.row_factory = sqlite3.Row
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS documents (
          id TEXT PRIMARY KEY, source TEXT NOT NULL, kind TEXT NOT NULL,
          url TEXT NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
          created_at TEXT, updated_at TEXT, fetched_at TEXT NOT NULL,
          state TEXT, merged_at TEXT, parent TEXT, tags TEXT NOT NULL,
          metadata TEXT NOT NULL, content_hash TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS doc_dates ON documents(updated_at);
        CREATE INDEX IF NOT EXISTS doc_parent ON documents(parent);
        CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(id UNINDEXED,title,body,tags,tokenize='unicode61');
        CREATE TABLE IF NOT EXISTS checkpoints (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS edges (
          src TEXT, relation TEXT, dst TEXT, evidence TEXT, detail TEXT,
          PRIMARY KEY(src,relation,dst,evidence));
        CREATE INDEX IF NOT EXISTS edge_dst ON edges(dst);
        CREATE TABLE IF NOT EXISTS document_revisions (
          id TEXT NOT NULL, content_hash TEXT NOT NULL, observed_at TEXT NOT NULL,
          document TEXT NOT NULL, PRIMARY KEY(id,content_hash));
        CREATE TRIGGER IF NOT EXISTS revisions_no_update BEFORE UPDATE ON document_revisions
          BEGIN SELECT RAISE(ABORT, 'document revisions are immutable'); END;
        CREATE TRIGGER IF NOT EXISTS revisions_no_delete BEFORE DELETE ON document_revisions
          BEGIN SELECT RAISE(ABORT, 'document revisions are immutable'); END;
        """)

    def get_checkpoint(self, key, default=None):
        row = self.db.execute("SELECT value FROM checkpoints WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def checkpoint(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO checkpoints VALUES (?,?)", (key, json.dumps(value)))
        self.db.commit()

    def put(self, doc):
        doc = dict(doc)
        doc.setdefault("body", "")
        doc.setdefault("title", "")
        doc["body"] = doc["body"] or ""
        doc.setdefault("fetched_at", now())
        for k in ("created_at", "updated_at", "state", "merged_at", "parent"):
            doc.setdefault(k, None)
        doc["tags"] = json.dumps(tags_for(doc["title"] + " " + doc["body"]))
        doc["metadata"] = json.dumps(doc.get("metadata", {}), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        # Fetch timestamps are not content changes. Source dates and state ARE:
        # a PR merge or paper revision must survive a later refresh.
        doc["content_hash"] = content_fingerprint(doc)
        old = self.db.execute("SELECT * FROM documents WHERE id=?", (doc["id"],)).fetchone()
        for revision in ([dict(old)] if old else []) + [doc]:
            # Older installations used a different hash formula. Normalize the
            # revision identity without losing the original legacy hash or body.
            identity = content_fingerprint(revision)
            if revision["content_hash"] != identity:
                revision["legacy_content_hash"] = revision["content_hash"]
                revision["content_hash"] = identity
            self.db.execute("INSERT OR IGNORE INTO document_revisions VALUES (?,?,?,?)",
                            (revision["id"], identity, revision["fetched_at"],
                             json.dumps(revision, sort_keys=True, ensure_ascii=False)))
        columns = [r[1] for r in self.db.execute("PRAGMA table_info(documents)")]
        self.db.execute("INSERT OR REPLACE INTO documents (" + ",".join(columns) + ") VALUES (" + ",".join("?" for _ in columns) + ")", [doc[c] for c in columns])
        self.db.execute("DELETE FROM search_index WHERE id=?", (doc["id"],))
        self.db.execute("INSERT INTO search_index VALUES (?,?,?,?)", (doc["id"], doc["title"], doc["body"], doc["tags"]))
        self.db.execute("DELETE FROM edges WHERE evidence=? AND relation IN ('mentions','links_to','child_of')", (doc["id"],))
        for tag in json.loads(doc["tags"]):
            self.edge(doc["id"], "mentions", "entity:" + tag, doc["id"], {"extraction": "keyword; not a causal claim"})
        for url in set(re.findall(r'https?://[^\s<>"\)\]]+', doc["body"])):
            self.edge(doc["id"], "links_to", link_identity(url.rstrip(".,;")), doc["id"], {"url": url.rstrip(".,;")})
        if doc["parent"]:
            self.edge(doc["id"], "child_of", doc["parent"], doc["id"], {})

    def edge(self, src, relation, dst, evidence, detail):
        self.db.execute("INSERT OR REPLACE INTO edges VALUES (?,?,?,?,?)", (src, relation, dst, evidence, json.dumps(detail)))

    def get(self, id):
        r = self.db.execute("SELECT * FROM documents WHERE id=?", (id,)).fetchone()
        return self.decode(r) if r else None

    def revisions(self, id):
        """Immutable content revisions, including the previous version on upgrade."""
        return [self.decode(json.loads(row[0])) for row in self.db.execute(
            "SELECT document FROM document_revisions WHERE id=? ORDER BY observed_at,rowid", (id,))]

    @staticmethod
    def decode(row):
        d = dict(row)
        for k in ("tags", "metadata"):
            if k in d:
                d[k] = json.loads(d[k])
        return d

    def search(self, query="", match="any", after=None, before=None, date_field="updated_at", kind=None, state=None, tags=None, limit=20, sort="relevance", id_prefix=None):
        if date_field not in {"created_at", "updated_at", "merged_at", "fetched_at"}:
            raise ValueError("Invalid date field")
        where, args = [], []
        join = ""
        rank = "0 AS rank"
        if query.strip():
            join = " JOIN search_index s ON d.id=s.id"
            where.append("search_index MATCH ?")
            args.append(fts_query(query, match))
            rank = "bm25(search_index,0,5,1,2) AS rank"
        for val, op in ((after, ">="), (before, "<")):
            if val:
                dt.datetime.fromisoformat(val.replace("Z", "+00:00"))
                where.append("d." + date_field + op + "?")
                args.append(val)
        for key, value in (("kind", kind), ("state", state)):
            if value:
                where.append("d." + key + "=?")
                args.append(value)
        if id_prefix:
            where.append("substr(d.id,1,?)=?")
            args.extend([len(id_prefix), id_prefix])
        for tag in tags or []:
            where.append("EXISTS(SELECT 1 FROM json_each(d.tags) WHERE value=?)")
            args.append(tag.lower())
        order = "d." + date_field + " DESC" if sort == "newest" else "rank,d.updated_at DESC"
        sql = "SELECT d.*," + rank + " FROM documents d" + join + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY " + order + " LIMIT ?"
        args.append(min(max(int(limit), 1), 500))
        return [self.decode(r) for r in self.db.execute(sql, args)]

    def graph(self, node, limit=100):
        return [dict(r) for r in self.db.execute("SELECT * FROM edges WHERE src=? OR dst=? LIMIT ?", (node, node, limit))]

    def stats(self):
        return {"documents": self.db.execute("SELECT count(*) FROM documents").fetchone()[0],
                "by_kind": {r[0]: r[1] for r in self.db.execute("SELECT kind,count(*) FROM documents GROUP BY kind")},
                "edges": self.db.execute("SELECT count(*) FROM edges").fetchone()[0],
                "checkpoints": {r[0]: json.loads(r[1]) for r in self.db.execute("SELECT * FROM checkpoints")}}
