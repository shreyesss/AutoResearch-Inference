"""Persistent successful-response cache and atomic provider budgets (stdlib only)."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import sqlite3
import time


def policy():
    return json.loads((Path(__file__).resolve().parents[1] / "config/retrieval.json").read_text())


class Cache:
    def __init__(self, root):
        self.root = Path(root) / "cache"
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "index.sqlite"
        with self.connection() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, namespace TEXT, value TEXT, fetched REAL, expires REAL);
            CREATE TABLE IF NOT EXISTS events (namespace TEXT, event TEXT, at REAL);
            CREATE TABLE IF NOT EXISTS usage (provider TEXT, at REAL);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(str(self.path), timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def call(self, namespace, request, fetch, ttl, refresh=False):
        key = hashlib.sha256(json.dumps([namespace, request], sort_keys=True).encode()).hexdigest()
        # Serialize identical misses across CLI processes, without holding a DB transaction during I/O.
        with (self.root / (key + ".lock")).open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            with self.connection() as db:
                row = db.execute("SELECT value,fetched,expires FROM responses WHERE key=?", (key,)).fetchone()
                hit = bool(row and not refresh and row[2] > time.time())
                db.execute("INSERT INTO events VALUES (?,?,?)", (namespace, "hit" if hit else "miss", time.time()))
            if hit:
                value, fetched, expires = json.loads(row[0]), row[1], row[2]
            else:
                value = fetch()  # Exceptions never become successful cache entries.
                fetched = time.time()
                expires = fetched + (min(ttl, 300) if isinstance(value, dict) and "http_error" in value else ttl)
                with self.connection() as db:
                    db.execute("INSERT OR REPLACE INTO responses VALUES (?,?,?,?,?)", (key, namespace, json.dumps(value), fetched, expires))
            return value, {"hit": hit, "key": key, "fetched_at": datetime.fromtimestamp(fetched, timezone.utc).isoformat(),
                           "expires_at": datetime.fromtimestamp(expires, timezone.utc).isoformat()}

    def reserve(self, provider):
        limits = policy()["budgets"][provider]
        now = time.time()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            total = db.execute("SELECT count(*) FROM usage WHERE provider=?", (provider,)).fetchone()[0]
            daily = db.execute("SELECT count(*) FROM usage WHERE provider=? AND at>?", (provider, now - 86400)).fetchone()[0]
            if total >= limits["total"] or daily >= limits["rolling_24h"]:
                raise RuntimeError(provider + " local request budget exhausted; inspect research.cache_status and config/retrieval.json")
            db.execute("INSERT INTO usage VALUES (?,?)", (provider, now))

    def status(self):
        with self.connection() as db:
            counts = {n: {"hit": 0, "miss": 0} for n, in db.execute("SELECT DISTINCT namespace FROM events")}
            for namespace, event, count in db.execute("SELECT namespace,event,count(*) FROM events GROUP BY namespace,event"):
                counts[namespace][event] = count
            usage = {p: {"attempts": db.execute("SELECT count(*) FROM usage WHERE provider=?", (p,)).fetchone()[0],
                         "rolling_24h": db.execute("SELECT count(*) FROM usage WHERE provider=? AND at>?", (p, time.time()-86400)).fetchone()[0],
                         "limits": limits} for p, limits in policy()["budgets"].items()}
            return {"path": str(self.path), "requests": counts, "budgets": usage,
                    "note": "Local attempted requests since installation, including failures; not provider account credits. Hits do not spend requests."}
